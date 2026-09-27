import base64
import os
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

PUBLIC_BUCKET_NAME = "chefgemini-public-qwiklabs-gcp-01-0d643ff47544"


async def generate_recipe_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short video showcasing a recipe or culinary dish using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Args:
        prompt: A descriptive text prompt of the dish or recipe video to generate (e.g., 'A 5-second video of a freshly baked margherita pizza with steaming cheese').
        tool_context: The ADK tool context for saving artifacts.

    Returns:
        The public HTTPS URL of the video uploaded to Cloud Storage.
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-01-0d643ff47544")
    client = genai.Client(
        vertexai=True,
        project=project,
        location="global",
    )

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    if hasattr(interaction, "output_video") and interaction.output_video and getattr(interaction.output_video, "data", None):
        video_bytes = base64.b64decode(interaction.output_video.data)
    elif hasattr(interaction, "steps"):
        for step in getattr(interaction, "steps", []):
            if getattr(step, "type", None) == "model_output":
                for content_item in getattr(step, "content", []):
                    if getattr(content_item, "type", None) == "video":
                        data_val = getattr(content_item, "bytes", None) or getattr(content_item, "data", None)
                        if data_val:
                            video_bytes = base64.b64decode(data_val)
                            break
                if video_bytes:
                    break

    if not video_bytes:
        raise RuntimeError("Failed to retrieve generated video bytes from gemini-omni-flash-preview interaction.")

    filename = f"recipe_video_{uuid.uuid4().hex[:8]}.mp4"

    # 1) Save with tool_context.save_artifact so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2) Upload video bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(PUBLIC_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{PUBLIC_BUCKET_NAME}/{filename}"
    return public_url
