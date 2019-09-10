# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# The entire source code is OSSRPL except 'makeqr and getqr' which is MPL
# License: MPL and OSSRPL
""" Userbot module containing commands related to QR Codes. """

import os
from asyncio import sleep
from datetime import datetime
from requests import post, get
from userbot import CMD_HELP, CMDPREFIX
from userbot.events import register, errors_handler


def progress(current, total):
    # Calculate and return the download progress with given arguments
    print("Downloaded {} of {}\nCompleted {}".format(current, total,
                                                     (current / total) * 100))


@register(outgoing=True, pattern=f"^{CMDPREFIX}getqr$")
@errors_handler
async def parseqr(event):
    # For .getqr command, get QR Code content from the replied photo
    if event.fwd_from:
        return
    start = datetime.now()
    downloaded_file_name = await event.client.download_media(
        await event.get_reply_message(), progress_callback=progress)
    url = "https://api.qrserver.com/v1/read-qr-code/?outputformat=json"
    file = open(downloaded_file_name, "rb")
    files = {"file": file}
    resp = post(url, files=files).json()
    qr_contents = resp[0]["symbol"][0]["data"]
    file.close()
    os.remove(downloaded_file_name)
    end = datetime.now()
    duration = (end - start).seconds
    await event.edit("Obtained QRCode contents in {} seconds.\n{}".format(
        duration, qr_contents))


@register(outgoing=True, pattern=f"^{CMDPREFIX}makeqr(?: |$)([\s\S]*)")
@errors_handler
async def make_qr(event):
    # For .makeqr command, make a QR Code containing the given content
    if event.fwd_from:
        return
    start = datetime.now()
    input_str = event.pattern_match.group(1)
    message = "SYNTAX: `.makeqr <long text to include>`"
    reply_msg_id = None
    if input_str:
        message = input_str
    elif event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        reply_msg_id = previous_message.id
        if previous_message.media:
            downloaded_file_name = await event.client.download_media(
                previous_message, progress_callback=progress)
            m_list = None
            with open(downloaded_file_name, "rb") as file:
                m_list = file.readlines()
            message = ""
            for media in m_list:
                message += media.decode("UTF-8") + "\r\n"
            os.remove(downloaded_file_name)
        else:
            message = previous_message.message

    url = "https://api.qrserver.com/v1/create-qr-code/?data={}&\
size=200x200&charset-source=UTF-8&charset-target=UTF-8\
&ecc=L&color=0-0-0&bgcolor=255-255-255\
&margin=1&qzone=0&format=jpg"

    resp = get(url.format(message), stream=True)
    required_file_name = "temp_qr.webp"
    with open(required_file_name, "w+b") as file:
        for chunk in resp.iter_content(chunk_size=128):
            file.write(chunk)
    await event.client.send_file(
        event.chat_id,
        required_file_name,
        reply_to=reply_msg_id,
        progress_callback=progress,
    )
    os.remove(required_file_name)
    duration = (datetime.now() - start).seconds
    await event.edit("Created QRCode in {} seconds".format(duration))
    await sleep(5)
    await event.delete()


CMD_HELP.update({
    'getqr':
    ".getqr"
    "\nUsage: Get the QR Code content from the replied QR Code."
})
CMD_HELP.update({
    'makeqr':
    ".makeqr <content>)"
    "\nUsage: Make a QR Code from the given content."
    "\nExample: .makeqr www.google.com"
})
