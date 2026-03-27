import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import subprocess
from bs4 import BeautifulSoup
import win32com.client  # NEW: to resolve LNK shortcut to real EXE


# -------------------------------------------------------
# FIXED: RESOLVE REAL EDGE EXE EVEN IF ONLY .LNK EXISTS
# -------------------------------------------------------
def _get_edge_path():
    """Find the real Microsoft Edge executable path even if system shows only .lnk"""

    shortcut_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk"

    if os.path.exists(shortcut_path):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            edge_exe = shortcut.Targetpath

            if edge_exe and os.path.exists(edge_exe):
                return edge_exe
        except:
            pass

    # Fallback (rare)
    possible_paths = [
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]

    for p in possible_paths:
        if os.path.exists(p):
            return p

    raise FileNotFoundError("Microsoft Edge executable not found.")



# -------------------------------------------------------
# YOUTUBE TOOL (NOW 100% WORKING)
# -------------------------------------------------------
@function_tool()
async def open_youtube(context: RunContext, query: str = "") -> str:
    """Open YouTube or play a video using Microsoft Edge"""
    logging.info(f"Tool called: open_youtube(query='{query}')")

    try:
        edge = _get_edge_path()

        if query.strip() == "":
            subprocess.Popen([edge, "https://www.youtube.com"])
            return "YouTube homepage opened in Microsoft Edge."

        # YouTube search → get first result
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                if "/watch?v=" in link["href"]:
                    video_url = f"https://www.youtube.com{link['href']}"
                    subprocess.Popen([edge, video_url])
                    return f"Playing '{query}' on YouTube."

        # fallback
        subprocess.Popen([edge, search_url])
        return f"Opened YouTube search results for '{query}'."

    except Exception as e:
        logging.error(f"Error in open_youtube: {e}")
        return f"Failed to open YouTube: {e}"



# -------------------------------------------------------
# INSTAGRAM TOOL — FIXED
# -------------------------------------------------------
@function_tool()
async def open_instagram(context: RunContext) -> str:
    """
    Open Instagram using the real Edge executable, resolved from the .lnk file.
    """
    logging.info("Tool called: open_instagram()")

    try:
        # Resolve real Edge EXE path
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Edge.lnk"
        )
        edge_exe = shortcut.Targetpath

        if not os.path.exists(edge_exe):
            return "Could not find Microsoft Edge executable."

        # Open Instagram
        subprocess.Popen([edge_exe, "https://www.instagram.com"])

        return "Instagram opened in Microsoft Edge."

    except Exception as e:
        logging.error(f"Error in open_instagram: {e}")
        return f"Failed to open Instagram: {e}"



# -------------------------------------------------------
# WEATHER TOOL
# -------------------------------------------------------
@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            return response.text.strip()
        return f"Could not retrieve weather for {city}."
    except Exception as e:
        return f"Error retrieving weather: {e}"



# -------------------------------------------------------
# WEB SEARCH TOOL
# -------------------------------------------------------
@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        return results
    except Exception as e:
        return f"Web search error: {e}"



# -------------------------------------------------------
# EMAIL TOOL
# -------------------------------------------------------
@function_tool()
async def send_email(
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            return "Email failed: Gmail credentials not set."

        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to_email
        msg["Subject"] = subject

        recipients = [to_email]

        if cc_email:
            msg["Cc"] = cc_email
            recipients.append(cc_email)

        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()

        return f"Email sent to {to_email}"

    except Exception as e:
        return f"Email sending error: {e}"
