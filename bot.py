import os
import tempfile
import telebot
from telebot import types
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODEL_PATH = "models/ghibli.ckpt"

bot = telebot.TeleBot(BOT_TOKEN)
sessions = {}

# Load Stable Diffusion
pipe = StableDiffusionPipeline.from_ckpt(MODEL_PATH, torch_dtype=torch.float16).to("cuda")

def ghibli_style(image_path, out_path):
    img = Image.open(image_path).convert("RGB")
    prompt = "Ghibli style portrait, vibrant, soft lighting"
    out = pipe(prompt=prompt, image=img, num_inference_steps=30).images[0]
    out.save(out_path)

def make_video(image_path, audio_path, out_path):
    audio = AudioFileClip(audio_path)
    img_clip = ImageClip(image_path).set_duration(audio.duration).set_fps(24)
    img_clip = img_clip.set_audio(audio)
    img_clip.write_videofile(out_path, codec="libx264", audio_codec="aac")

# Handlers
@bot.message_handler(content_types=["photo", "audio"])
def collect_media(msg):
    user = msg.from_user.id
    if user not in sessions:
        sessions[user] = {}
    s = sessions[user]

    if msg.content_type == "photo":
        s["photo_file"] = bot.download_file(bot.get_file(msg.photo[-1].file_id).file_path)
    elif msg.content_type == "audio":
        s["audio_file"] = bot.download_file(bot.get_file(msg.audio.file_id).file_path)

    if "photo_file" in s and "audio_file" in s:
        bot.send_message(user, "✨ Creating your Ghibli-style video... this may take a bit!")
        with tempfile.TemporaryDirectory() as tmp:
            p_path = os.path.join(tmp, "in.jpg")
            a_path = os.path.join(tmp, "in.mp3")
            g_path = os.path.join(tmp, "ghibli.jpg")
            v_path = os.path.join(tmp, "final.mp4")

            with open(p_path, "wb") as f: f.write(s["photo_file"])
            with open(a_path, "wb") as f: f.write(s["audio_file"])

            ghibli_style(p_path, g_path)
            make_video(g_path, a_path, v_path)

            bot.send_video(user, open(v_path, "rb"))
        sessions.pop(user)

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "Send a photo + an audio file and I'll return your Ghibli-style video!")

bot.infinity_polling()
