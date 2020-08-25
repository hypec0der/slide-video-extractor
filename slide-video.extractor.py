
import argparse
import urllib3
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


def download_video(url, video_path):

    c = urllib3.PoolManager()

    with open(video_path, 'wb') as path:

        with c.request('GET', url, preload_content=False) as video:

            while True:

                data = video.read(65565)

                if not data:

                    break
                    
                path.write(data)

        video.release_conn()


def main():

    parser = argparse.ArgumentParser(description='Slide extractor from video')
    parser.add_argument('-u','--url',dest='url',required=True,help='Insert url (or local path) where video is located')
    parser.add_argument('-d','--dir',dest='path',default=os.getcwd(),help='Enter path where both video and slides will be stored')
    parser.add_argument('-n','--name',dest='name',default='temp.mp4',help='Name the video that will be stored in directory')
    parser.add_argument('-r','--del',dest='remove',default=False,action='store_true',help='Remove video after processing (default false)')

    args = parser.parse_args()

    if re.match(url_validation, f'{args.url}/{args.video}'):
        download_video(args.url, args.path)

    if args.remove:
        os.remove(f'{args.path}/{args.video}')
    


if __name__ == "__main__":
    main()