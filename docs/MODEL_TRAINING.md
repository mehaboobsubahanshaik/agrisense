# Training the crop disease model

The stack runs without weights (OpenCV fallback). This is how to replace it with a real
YOLOv11 model and report accuracy honestly.

## 1. Datasets

| Dataset | Content | Where |
|---|---|---|
| PlantVillage | 54k lab images, 38 classes, 14 crops | Kaggle: `abdallahalidev/plantvillage-dataset` |
| PlantDoc | 2.6k **field** images, 27 classes | github.com/pratikkayal/PlantDoc-Dataset |
| Rice Leaf Diseases | blast, brown spot, bacterial blight | UCI / Kaggle |
| Fall armyworm (maize) | whorl damage in the field | Kaggle: `nirmalsankalana/*` |

PlantVillage alone overfits badly: its images are single leaves on a uniform background, and field
photos from a phone look nothing like that. **Always mix in PlantDoc or your own field photos**, or
the reported accuracy will not survive contact with a farmer's camera.

## 2. Class map

Train with class names the backend already knows (`ai-service/app/detector.py::CLASS_ALIAS`):

```
rice_blast, bacterial_leaf_blight, leaf_spot, leaf_rust, powdery_mildew,
late_blight, early_blight, pest_damage, nutrient_deficiency, healthy
```

Anything else still works — unmapped names fall through to the generic leaf-spot remedy card, so add
the new key to `backend/app/knowledge/agri_docs.py::DISEASE_LIBRARY` when you add a class.

## 3. Dataset layout

```
datasets/crop-disease/
├── data.yaml
├── images/{train,val,test}/
└── labels/{train,val,test}/       # YOLO format: class cx cy w h (normalised)
```

```yaml
# data.yaml
path: ./datasets/crop-disease
train: images/train
val: images/val
test: images/test
names:
  0: rice_blast
  1: bacterial_leaf_blight
  2: leaf_spot
  3: leaf_rust
  4: powdery_mildew
  5: late_blight
  6: early_blight
  7: pest_damage
  8: nutrient_deficiency
  9: healthy
```

## 4. Train

```bash
pip install ultralytics
yolo detect train \
  model=yolo11s.pt data=datasets/crop-disease/data.yaml \
  epochs=120 imgsz=640 batch=16 patience=25 \
  hsv_h=0.02 hsv_s=0.7 hsv_v=0.4 degrees=15 scale=0.5 fliplr=0.5 mosaic=1.0 \
  project=runs name=agrisense
```

The HSV augmentation range matters more than epochs here: field photos vary enormously in light
temperature, and a model trained without it collapses on evening photos.

## 5. Evaluate and report

```bash
yolo detect val model=runs/agrisense/weights/best.pt data=datasets/crop-disease/data.yaml split=test
```

Report **per-class precision, recall and mAP50-95 on the held-out test split**, and a confusion
matrix. Two numbers that matter more than headline mAP:

* **Recall on high-severity classes** — a missed blast costs a season; a false positive costs one
  unnecessary spray.
* **Field-image accuracy separately from lab-image accuracy.** Quote both. A 99% PlantVillage
  number next to a 61% PlantDoc number is a more credible result than one blended figure.

## 6. Deploy

```bash
cp runs/agrisense/weights/best.pt models/crop_disease_yolo11.pt
docker compose restart ai-service
curl http://localhost:8080/ai/health      # {"weights_present": true, ...}
```

Confidence threshold is `YOLO_CONF` (default 0.35) in `docker-compose.yml`.

## 7. Optional: ONNX for slower hardware

```bash
yolo export model=models/crop_disease_yolo11.pt format=onnx opset=12 simplify=True
```

Roughly 2–3× faster on CPU-only boxes, which is what a district office will actually run.
