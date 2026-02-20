# Media Generation

## Image Generation
Generate images using `imagen-3.0-generate-001`.

```python
from google import genai
from google.genai.types import GenerateImagesConfig

client = genai.Client()

image_response = client.models.generate_images(
    model="imagen-3.0-generate-001",
    prompt="A dog reading a newspaper",
    config=GenerateImagesConfig(image_size="2K"),
)
image_response.generated_images[0].image.save("dog_newspaper.png")
```

## Image Editing (Inpainting)
```python
from google import genai
from google.genai.types import RawReferenceImage, MaskReferenceImage, MaskReferenceConfig, EditImageConfig, Image

client = genai.Client()

raw_ref = RawReferenceImage(
    reference_image=Image.from_file(location="fruit.png"),
    reference_id=0,
)
mask_ref = MaskReferenceImage(
    reference_id=1,
    reference_image=None,
    config=MaskReferenceConfig(mask_mode="MASK_MODE_FOREGROUND", mask_dilation=0.1),
)

image_response = client.models.edit_image(
    model="imagen-3.0-capability-001",
    prompt="A small white ceramic bowl with lemons and limes",
    reference_images=[raw_ref, mask_ref],
    config=EditImageConfig(edit_mode="EDIT_MODE_INPAINT_INSERTION"),
)
image_response.generated_images[0].image.save("fruit_edit.png")
```

## Video Generation
Generate video using the Veo model.

```python
import time
from google import genai
from google.genai.types import GenerateVideosConfig

client = genai.Client()

operation = client.models.generate_videos(
    model="veo-3.1-generate-001",
    prompt="a cat reading a book",
    config=GenerateVideosConfig(
        aspect_ratio="16:9",
        output_gcs_uri="gs://your-bucket/your-prefix",
    ),
)

while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)

if operation.response:
    print(operation.result.generated_videos[0].video.uri)
```
