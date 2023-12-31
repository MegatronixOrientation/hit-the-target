import cv2
import cvzone
import numpy as np
from cvzone.ColorModule import ColorFinder
import pickle

cap = cv2.VideoCapture(0)
frameCounter = 0
cornerPoints = [[377, 52], [944, 71], [261, 624], [1058, 612]]
colorFinder = ColorFinder(False)
hsvVals = {'hmin': 30, 'smin': 34, 'vmin': 0, 'hmax': 41, 'smax': 255, 'vmax': 255}
countHit = 0
imgListBallsDetected = []
hitDrawBallInfoList = []
totalScore1 = 0
totalScore2 = 0

with open('polygons', 'rb') as f:
    polygonsWithScore = pickle.load(f)


def getBoard(img):
    width, height = int(400 * 1.5), int(380 * 1.5)
    pts1 = np.float32(cornerPoints)
    pts2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    imgOutput = cv2.warpPerspective(img, matrix, (width, height))
    for x in range(4):
        cv2.circle(img, (cornerPoints[x][0], cornerPoints[x][1]), 15, (0, 255, 0), cv2.FILLED)

    return imgOutput


def detectColorDarts(img):
    imgBlur = cv2.GaussianBlur(img, (7, 7), 2)
    imgColor, mask = colorFinder.update(imgBlur, hsvVals)
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.medianBlur(mask, 9)
    mask = cv2.dilate(mask, kernel, iterations=4)
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask

# Initialize player turn and hit counts
player_turn = 1  # Player 1 starts
player1_hits = 0
player2_hits = 0

while True:

    frameCounter += 1
    if frameCounter == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        frameCounter = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    success, img = cap.read()
    imgBoard = getBoard(img)
    mask = detectColorDarts(imgBoard)

    for x, img in enumerate(imgListBallsDetected):
        mask = mask - img

    imgContours, conFound = cvzone.findContours(imgBoard, mask, 3500)

    if conFound:
        countHit += 1
        if countHit == 10:
            imgListBallsDetected.append(mask)
            countHit = 0
            for polyScore in polygonsWithScore:
                center = conFound[0]['center']
                poly = np.array([polyScore[0]], np.int32)
                inside = cv2.pointPolygonTest(poly, center, False)
                if inside == 1:
                    hitDrawBallInfoList.append([conFound[0]['bbox'], conFound[0]['center'], poly])
                    if player_turn == 1:
                        totalScore1 += polyScore[1]
                        player1_hits += 1
                        if player1_hits == 3:
                            # Switch to player 2's turn
                            player_turn = 2
                            player1_hits = 0
                    else:
                        totalScore2 += polyScore[1]
                        player2_hits += 1
                        if player2_hits == 3:
                            # Switch to player 1's turn
                            player_turn = 1
                            player2_hits = 0

            imgBlank = np.zeros((imgContours.shape[0], imgContours.shape[1], 3), np.uint8)

            for bbox, center, poly in hitDrawBallInfoList:
                cv2.rectangle(imgContours, bbox, (255, 0, 255), 2)
                cv2.circle(imgContours, center, 5, (0, 255, 0), cv2.FILLED)
                cv2.drawContours(imgBlank, [poly], -1, color=(0, 255, 0), thickness=cv2.FILLED)

            imgBoard = cv2.addWeighted(imgBoard, 0.7, imgBlank, 0.5, 0)

            player_turn_text = f'Player Turn: {player_turn}'
            imgBoard, _ = cvzone.putTextRect(imgBoard, player_turn_text,
                                             (10, 40), scale=2, offset=20)

            imgBoard, _ = cvzone.putTextRect(imgBoard, f'Player 1 Score: {totalScore1}',
                                             (10, 80), scale=2, offset=20)

            imgBoard, _ = cvzone.putTextRect(imgBoard, f'Player 2 Score: {totalScore2}',
                                             (10, 120), scale=2, offset=20)

            imgStack = cvzone.stackImages([imgContours, imgBoard], 2, 1)

            cv2.imshow("Image Contours", imgStack)

            if cv2.waitKey(1) == 27:
                break

cap.release()
cv2.destroyAllWindows()