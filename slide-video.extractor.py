
import tensorflow as tf
import argparse
import urllib3
import math
import cv2
import sys
import re
import os


url_validation = re.compile(
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



def download_video(url, path, name, verbose=False):

    c = urllib3.PoolManager()

    packet = 0

    print(f'Start downloading from url -> {url}')

    with open(f'{path}/{name}.mp4', 'wb') as path:

        with c.request('GET', url, preload_content=False) as video:

            if verbose:

                print(c.headers)

            content_length = int(video.headers.get('Content-Length'))

            while True:

                data = video.read(65565)

                if not data:

                    break

                progress = math.floor(((packet * 65565) / content_length) * 100)

                print(f"{'='*progress}>", end='\r')

                packet = packet + 1
                    
                path.write(data)

        print('\n')

        video.release_conn()



def frame_capture(path, name, threshold, fps):

    with VideoFramesComp(path, name, fps=fps) as video:

        current_frame = video.nextframe()

        while video.isOpened():

            new_frame = video.nextframe()

            progress = math.floor((video.frameId / video.totalFrames)*100)

            print(f'{"="*progress}>', end='\r')

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
        if re.match(url_validation, args.url):
            download_video(args.url, args.path, args.name)

        # Convert each frame in jpg format
        frame_capture(args.path, args.name, threshold=args.threshold, fps=args.fps)

        # If remove is True then remove video
        if args.remove:
            os.remove(f'{args.path}/{args.name}')
    
    except KeyboardInterrupt as interrupt:
        sys.exit(0)



if __name__ == "__main__":
    main()
