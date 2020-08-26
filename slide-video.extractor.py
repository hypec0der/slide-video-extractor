
import tensorflow as tf
import argparse
import urllib3
import math
import cv2
import sys
import re
import os


URL_VALIDATION = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class VideoFramesComp():

    def __init__(self, path, name, ext='.mp4', fps=60):
        
        self.path = path
        self.name = name
        self.ext = ext
        self.fps = fps  #  Frame rate.
    

    def nextframe(self):

        while True:

            # Current position of the video file in milliseconds or video capture timestamp.
            self.frameId = self.vidObj.get(cv2.CAP_PROP_POS_FRAMES)

            success, new_frame = self.vidObj.read()

            if self.frameId % math.floor(self.frameRate) == 0:
                
                return tf.constant(new_frame)



    def compare(self, img1, img2, threshold=.9):

        ssim1 = tf.image.ssim(img1, img2, max_val=255)

        return True if ssim1 >= threshold else False


    def isOpened(self):

        return self.vidObj.isOpened()

    
    def saveframe(self, img1, ext='.jpg'):

        cv2.imwrite(f'{self.path}/{self.name}_{self.frameId}{ext}', img1.numpy())

    
    def print_progress(self):

        progress = math.floor((self.frameId / self.totalFrames)*100)

        print(f"{'='*progress}> {' '*(100-progress)} {progress}%", end='\r')


    def __enter__(self):

        self.vidObj = cv2.VideoCapture(f'{self.path}/{self.name}{self.ext}')
        #  Frame rate.
        self.frameRate = self.vidObj.get(cv2.CAP_PROP_FPS) * self.fps  
        # Get total number of frames
        self.totalFrames = self.vidObj.get(cv2.CAP_PROP_FRAME_COUNT)

        return self


    def __exit__(self, type, value, traceback):

        self.vidObj.release()

        cv2.destroyAllWindows()



class DownloadVideo(urllib3.PoolManager):


    _FRAME_LENGTH = 65565

    request_headers = None
    frame_counter = 0
    url = None


    def __init__(self, url):

        super().__init__()

        self.url = url


    def nextframe(self):

        self.frame_counter += 1

        self.current_frame = self.request.read(DownloadVideo._FRAME_LENGTH)

        return None if not self.current_frame else self.current_frame


    def print_progress(self):

        content_length = int(self.request_headers.get('Content-Length', 0))

        progress = math.floor(((self.frame_counter * DownloadVideo._FRAME_LENGTH) / content_length) * 100)

        print(f"{'='*progress}> {' '*(100-progress)} {progress}%", end='\r')


    def __enter__(self):

        self.request = self.request('GET', self.url, preload_content=False)

        self.request_headers = self.request.headers

        assert self.request == 200, Exception()

        return self

    
    def __exit__(self, type, value, traceback):

        self.request.release_conn()



def download_video(url, path, name):

    try:
        
        with DownloadVideo(url) as video_download:

            try:

                with open(f'{path}/{name}.mp4', 'wb') as path:

                    while video_download.nextframe():
                
                        video_download.print_progress()

                        path.write(video_download.current_frame)

            except:

                print(f'Cannot open {path}/{name}')

    except Exception():

        print(f'Cannot download video from {url}')



def frame_capture(path, name, threshold, fps):

    with VideoFramesComp(path, name, fps=fps) as video:

        current_frame = video.nextframe()

        while video.isOpened():

            new_frame = video.nextframe()

            video.print_progress()

            if video.compare(current_frame, new_frame, threshold) is False:

                video.saveframe(current_frame)

                current_frame = new_frame



def main():

    parser = argparse.ArgumentParser(description='Slide extractor from video')
    parser.add_argument('-u','--url',dest='url',help='Insert url (or local path) where video is located')
    parser.add_argument('-d','--dir',dest='path',default=os.getcwd(),help='Enter path where both video and slides will be stored')
    parser.add_argument('-n','--name',dest='name',default='temp',help='Name the video that will be stored in directory')
    parser.add_argument('-r','--del',dest='remove',default=False,action='store_true',help='Remove video after processing it (default false)')
    parser.add_argument('-f','--fps',dest='fps',default=50,help='Select frame every n-th second')
    parser.add_argument('-t','--thold',dest='threshold',default=.9,help='Select threshold 0 < t <= 1 (sometimes 0.9 is good for slides)')
    parser.add_argument('-s','--start',dest='start',default=0,help='Select ')
    parser.add_argument('-v','--verbose',dest='verbose',action='store_true',default=False)

    args = parser.parse_args()

    try:

        # Download video from url
        if re.match(URL_VALIDATION, args.url):

            print(f'Start downloading video from url {args.url}\n')                
            
            download_video(args.url, args.path, args.name)

            print('Download complete! Start analyzing video and extract slides ... \n')


        # Convert each frame in jpg format
        if args.path is not None:
            
            frame_capture(args.path, args.name, threshold=args.threshold, fps=args.fps)


        # If remove is True then remove video
        if args.remove:

            os.remove(f'{args.path}/{args.name}.mp4')
    

    except KeyboardInterrupt as interrupt:
        sys.exit(0)



if __name__ == "__main__":
    main()





'''def download_video(url, path, name):

    c = urllib3.PoolManager()
    # Packet received counter
    packet = 0

    print(f'Start downloading from url -> {url}')

    # Open file in write/binary mode
    with open(f'{path}/{name}.mp4', 'wb') as path:
    
        with c.request('GET', url, preload_content=False) as video:

            if video.status != 200:

                raise Exception(f'Cannot download file from url {url}')

            content_length = int(video.headers.get('Content-Length'))

            while True:

                data = video.read(FRAME)

                if not data:

                    break
                        
                # Print progress 
                progress = math.floor(((packet * FRAME) / content_length) * 100)

                print(f"{'='*progress}> {' '*(100-progress)} {progress}%", end='\r')
                    
                packet = packet + 1

                # Write packet data into file video
                path.write(data)

            print('\n Download completed!')'''