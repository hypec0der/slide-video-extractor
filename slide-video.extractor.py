
import tensorflow as tf
import argparse
import urllib3
import math
import cv2
import re
import os


url_validation = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def download_video(url, path, name):

    c = urllib3.PoolManager()

    with open(f'{path}/{name}', 'wb') as path:

        with c.request('GET', url, preload_content=False) as video:

            while True:

                data = video.read(65565)

                if not data:

                    break
                    
                path.write(data)

        video.release_conn()


def frame_capture(path, name, threshold=.9, fps=50):

    vidObj = cv2.VideoCapture(f'{path}/{name}')

    frameRate = vidObj.get(cv2.CAP_PROP_FPS) * fps  #  Frame rate.

    success, current_frame = vidObj.read()

    counter = 0

    while vidObj.isOpened():

        frameId = vidObj.get(1)     # Current position of the video file in milliseconds or video capture timestamp.

        success, new_frame = vidObj.read()

        if frameId % math.floor(frameRate) == 0:

            ssim1 = tf.image.ssim(tf.constant(current_frame), tf.constant(new_frame), max_val=255)

            if ssim1 < threshold:

                cv2.imwrite(f'{path}/{name}_{counter}.jpg', current_frame)

                current_frame = new_frame
                
                counter = counter + 1

            print(ssim1)


    vidObj.release()

    cv2.destroyAllWindows()



def main():

    parser = argparse.ArgumentParser(description='Slide extractor from video')
    parser.add_argument('-u','--url',dest='url',required=True,help='Insert url (or local path) where video is located')
    parser.add_argument('-d','--dir',dest='path',default=os.getcwd(),help='Enter path where both video and slides will be stored')
    parser.add_argument('-n','--name',dest='name',default='temp.mp4',help='Name the video that will be stored in directory')
    parser.add_argument('-r','--del',dest='remove',default=False,action='store_true',help='Remove video after processing (default false)')

    args = parser.parse_args()

    if re.match(url_validation, args.url):
        download_video(args.url, args.path, args.name)

    frame_capture(args.path, args.name)

    if args.remove:
        os.remove(f'{args.path}/{args.name}')
    


if __name__ == "__main__":
    main()




'''def frame_capture(path, name, nth_frame=20):

    vidObj = cv2.VideoCapture(f'{path}/{name}')

    frameRate = vidObj.get(cv2.CAP_PROP_FPS) * nth_frame  #  Frame rate.

    cost_function = lambda f1, f2: sum(pow(f1-f2, 2)) / len(f1)

    counter = 0

    original = None

    while vidObj.isOpened():

        frameId = vidObj.get(1)     # Current position of the video file in milliseconds or video capture timestamp.

        success, image = vidObj.read()

        if not success:
            break

        if frameId % math.floor(frameRate) == 0:

            if original is None:
                original = image.flatten()

            else:

                waste = cost_function(original, image.flatten())

                if waste >= 10:

                    original = image.flatten()

                    counter = counter + 1

                    cv2.imwrite(f'{path}/{name}_{counter}.jpg', image)


                print(f'{counter}. waste={waste}')

            if counter == 20:
                break

    vidObj.release()
    cv2.destroyAllWindows()
'''