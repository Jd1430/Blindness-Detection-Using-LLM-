# Load BLIP model for image captioning
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration

def load_blip_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

def extract_image_description(image):
    processor, model = load_blip_model()
    image = image.convert('RGB')
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption
