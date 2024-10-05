#!/usr/bin/env python3
import argparse
import time
import logging
from pathlib import Path

import cv2
from tqdm import tqdm

logger = logging.getLogger()

TRAINING_IMG_WIDTH = 1920
TRAINING_IMG_HEIGHT = 1076
SKIP = 4
SUMMON2DARK = 25
DARK2SUMMON = 100

summon_flag = False


def find_notch(img_hsv):
    """
    直線検出で検出されなかったフチ幅を検出
    """
    edge_width = 150

    height, width = img_hsv.shape[:2]
    target_color = 0
    for lx in range(edge_width):
        img_hsv_x = img_hsv[:, lx:lx + 1]
        # ヒストグラムを計算
        hist = cv2.calcHist([img_hsv_x], [0], None, [256], [0, 256])
        # 最小値・最大値・最小値の位置・最大値の位置を取得
        _, maxVal, _, maxLoc = cv2.minMaxLoc(hist)
        if not (maxLoc[1] == target_color and maxVal > height * 0.4):
            break
    for ty in range(edge_width):
        img_hsv_y = img_hsv[ty: ty + 1, :]
        # ヒストグラムを計算
        hist = cv2.calcHist([img_hsv_y], [0], None, [256], [0, 256])
        # 最小値・最大値・最小値の位置・最大値の位置を取得
        _, maxVal, _, maxLoc = cv2.minMaxLoc(hist)
        if not (maxLoc[1] == target_color and maxVal > width * 0.4):
            break
    for rx in range(edge_width):
        img_hsv_x = img_hsv[:, width - rx - 1: width - rx]
        # ヒストグラムを計算
        hist = cv2.calcHist([img_hsv_x], [0], None, [256], [0, 256])
        # 最小値・最大値・最小値の位置・最大値の位置を取得
        _, maxVal, _, maxLoc = cv2.minMaxLoc(hist)
        if not (maxLoc[1] == target_color and maxVal > height * 0.4):
            break
    for by in range(edge_width):
        img_hsv_y = img_hsv[height - by - 1: height - by, :]
        # ヒストグラムを計算
        hist = cv2.calcHist([img_hsv_y], [0], None, [256], [0, 256])
        # 最小値・最大値・最小値の位置・最大値の位置を取得
        _, maxVal, _, maxLoc = cv2.minMaxLoc(hist)
        if not (maxLoc[1] == target_color and maxVal > width * 0.4):
            break

    return lx, ty, rx, by


def calc_black_whiteArea(bw_image):
    image_size = bw_image.size
    whitePixels = cv2.countNonZero(bw_image)
    # blackPixels = bw_image.size - whitePixels

    whiteAreaRatio = (whitePixels / image_size) * 100  # [%]
    # blackAreaRatio = (blackPixels/image_size)*100#[%]
    # print("White Area [%] : ", whiteAreaRatio)
    # print("Black Area [%] : ", blackAreaRatio)
    return whiteAreaRatio


NORMAL = 0
RESULT = 1
DARKNESS = 2


def recognize_screenshot(frame, name):
    global summon_flag
    h, w = frame.shape[:2]
    if w/h > 16/9.01:
        hscale = (1.0 * h) / TRAINING_IMG_HEIGHT
        resizeScale = 1 / hscale

        if resizeScale > 1:
            frame_resize = cv2.resize(
                                        frame, (0, 0),
                                        fx=resizeScale, fy=resizeScale,
                                        interpolation=cv2.INTER_CUBIC
                                        )
        else:
            frame_resize = cv2.resize(
                                        frame, (0, 0),
                                        fx=resizeScale, fy=resizeScale,
                                        interpolation=cv2.INTER_AREA
                                        )
    else:
        wscale = (1.0 * w) / TRAINING_IMG_WIDTH
        resizeScale = 1 / wscale

        if resizeScale > 1:
            frame_resize = cv2.resize(
                                        frame, (0, 0),
                                        fx=resizeScale, fy=resizeScale,
                                        interpolation=cv2.INTER_CUBIC
                                        )
        else:
            frame_resize = cv2.resize(
                                        frame, (0, 0),
                                        fx=resizeScale, fy=resizeScale,
                                        interpolation=cv2.INTER_AREA
                                        )

    # cv2.imwrite(name, frame_resize)
    # return
    height, width = frame_resize.shape[:2]
    # 編成ボタン描画完了をチェック
    hensei_button_file = Path(__file__).resolve().parent / Path("template/hensei_button.jpg")
    template = cv2.imread(str(hensei_button_file))
    res = cv2.matchTemplate(frame_resize[int(height*3/4): height, 0: int(width*1/3)], template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    if max_val <= 0.9:
        max_val_close = 0
    else:
        # 閉じるボタン描画完了をチェック
        close_button_file = Path(__file__).resolve().parent / Path("template/close_button.jpg")
        template_close = cv2.imread(str(close_button_file))
        res_close = cv2.matchTemplate(frame_resize[0: int(height*0.3), 0: int(width*1/5)], template_close, cv2.TM_CCOEFF_NORMED)
        _, max_val_close, _, _ = cv2.minMaxLoc(res_close)
    if summon_flag is False and max_val > 0.9 and max_val_close > 0.9:
        summon_flag = True
        cv2.imwrite(str(name), frame_resize)
        logger.debug("Found summon at %s", name)
        return RESULT
    elif summon_flag is True:
        # 暗転チェック
        img_gray = cv2.cvtColor(frame_resize, cv2.COLOR_BGR2GRAY)
        ret, thresh1 = cv2.threshold(img_gray, 30, 255, cv2.THRESH_BINARY)
        ratio = calc_black_whiteArea(thresh1[max(0, int(height/2-TRAINING_IMG_HEIGHT/2)): min(height, int(height/2+TRAINING_IMG_HEIGHT/2)):])
        if ratio < 1.0:
            summon_flag = False
            logger.debug("Found black area at %s", name)
            return DARKNESS
    return NORMAL


def main(args):
    out_dir = Path(args.output)
    if not out_dir.is_dir():
        out_dir.mkdir(parents=True)
    check_notch = False
    cap = cv2.VideoCapture(args.file_name)

    total_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    logger.debug(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    logger.debug(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.debug(cap.get(cv2.CAP_PROP_FPS))
    logger.debug(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))

    if args.ss is None:
        ss_frame = 0
    else:
        ss_frame = int(args.ss)
    if args.to is None:
        to_frame = total_frame_count
    else:
        to_frame = int(args.to)
    logger.debug("ss_frame = %f", ss_frame)
    logger.debug("to_frame = %f", to_frame)
    ret = cap.set(cv2.CAP_PROP_POS_FRAMES, ss_frame)
    logger.debug(ret)

    unixtime = int(time.time())  # 実行時刻のunixtimeを取得

    with tqdm(total=to_frame - ss_frame) as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            frame_id = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            if frame_id > to_frame:
                break
            if ret:
                # ノッチチェック
                if check_notch is False:
                    height, width = frame.shape[:2]
                    img_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    lx, ty, rx, by = find_notch(img_hsv)
                    check_notch = True
                    logger.debug("lx = %d, %ty = %d, rx = %d, by = %d", lx, ty, rx, by)
                    check_notch = True
                if (ss_frame <= frame_id <= to_frame) and (frame_id % SKIP == 0):
                    res = recognize_screenshot(frame[ty: height - by, lx: width - rx], out_dir / Path(f"{unixtime}_{frame_id/fps:0=7.2f}.jpg"))
                    if res == RESULT:
                        status = cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id + SUMMON2DARK)
                        pbar.update(SUMMON2DARK)
                        if status is False:
                            break
                    elif res == DARKNESS:
                        status = cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id + DARK2SUMMON)
                        pbar.update(DARK2SUMMON)
                        if status is False:
                            break
                pbar.update(1)
            else:
                break

    cap.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get summon screenshots from video"
    )
    parser.add_argument('file_name', help='video file')
    parser.add_argument(
        "-o",
        "--output",
        help="Output folder",
        default="video_screenshot",
    )
    parser.add_argument("-ss", help="Start")
    parser.add_argument("-to", help="End")
    parser.add_argument(
                        '--loglevel',
                        choices=('warning', 'debug', 'info'),
                        default='info'
                        )

    args = parser.parse_args()
    lformat = '%(name)s <%(filename)s-L%(lineno)s> [%(levelname)s] %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=lformat,
    )
    logger.setLevel(args.loglevel.upper())

    main(args)
