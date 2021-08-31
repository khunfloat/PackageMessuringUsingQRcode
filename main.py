import cv2
import numpy as np
from pyzbar.pyzbar import decode
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from pathlib import Path

collection = 'PackageInformation'
servicekey_path = Path('.', 'ServiceAccountKey.json')
image_path = './boxTH.png'

firebase_admin.initialize_app(credentials.Certificate(servicekey_path))
db = firestore.client()

class Package():
    
    def __init__(self, id):
        self.id = id
        self.dict = db.collection(collection).document(self.id).get().to_dict()
        self.activation = self.dict.get('activation')
        self.registeration = self.dict.get('registeration')
        
        self.IsActivatedIsRegistered = self.activation and self.registeration
        self.NotActivated = not self.activation
        self.IsActivatedNotRegistered = self.activation and (not self.registeration)
        
    def AddDimension(self, width, height, depth, weight):
        db.collection(collection).document(self.id).set({'height' : height, 
                                                        'width' : width,
                                                        'depth' : depth,
                                                        'weight' : weight}, merge=True)

class Image():

    def __init__(self, image):
        self.image = image
        self.ImageHasQRcode = True if len(decode(self.image)) != 0 else False
        self.qrcode_decode = decode(image)[0]
        self.qrcode_id = self.qrcode_decode.data.decode('utf-8')

def main():
          
    frame = Image(cv2.imread(image_path))

    if frame.ImageHasQRcode:
        
        qrcode = Package(frame.qrcode_id)
        
        if qrcode.IsActivatedIsRegistered:
        
            width, height, depth, weight = 0, 0, 0, 0
            
            pts = np.array([frame.qrcode_decode.polygon], np.int32).reshape((-1, 1, 2))
            dimension = pts[1][0][1] - pts[0][0][1]
            ratio = 5 / dimension
            
            gray = cv2.cvtColor(frame.image, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_TOZERO)
            contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                rect = cv2.minAreaRect(cnt)
                (x, y), (w, h), angle = rect

                # Get Width and Height of the Objects by applying the Ratio pixel to cm
                width, height = w * ratio, h * ratio

                # Display rectangle
                box = np.int0(cv2.boxPoints(rect))
                
                if (width > 6.4) and (height > 6.4):
                    cv2.circle(frame.image, (int(x), int(y)), 5, (0, 0, 255), -1)
                    cv2.polylines(frame.image, [box], True, (255, 0, 0), 2)
                    cv2.putText(frame.image, "Width {} cm".format(round(width, 2)), (int(x - 100), int(y - 20)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
                    cv2.putText(frame.image, "Height {} cm".format(round(height, 2)), (int(x - 100), int(y + 15)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
                    cv2.putText(frame.image, "Depth {} cm".format(round(depth, 2)), (int(x - 100), int(y + 50)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
                    cv2.putText(frame.image, "Weight {} cm".format(round(weight, 2)), (int(x - 100), int(y + 85)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
                    cv2.putText(frame.image, qrcode.id, (int(x - 100), int(y + 120)), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
                    
                    qrcode.AddDimension(width = width, height = height, depth = depth, weight = weight)

            cv2.imshow("Image", frame.image)
            # cv2.imshow('', gray)
            cv2.waitKey(0)
        elif qrcode.NotActivated:
            cv2.putText(frame.image, "QR isn't Activated", (40, 40), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)
        elif qrcode.IsActivatedNotRegistered:
            cv2.putText(frame.image, "QR doesn't have information", (40, 40), cv2.FONT_HERSHEY_PLAIN, 2, (100, 200, 0), 2)

    cv2.imshow("Image", frame.image)
    cv2.waitKey(0)
    
if __name__ == "__main__":
    main()