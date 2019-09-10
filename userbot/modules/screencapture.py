# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.
#
# The entire source code is OSSRPL except 'screencapture' which is MPL
# License: MPL and OSSRPL
""" Userbot module for ScreenshotLayer API """

import os
from requests import get
from userbot import SCREENSHOT_LAYER_ACCESS_KEY, CMD_HELP, CMDPREFIX
from userbot.events import register, errors_handler


@register(outgoing=True, pattern=f"^{CMDPREFIX}screencapture (.*)")
@errors_handler
async def capture(event):
    """ For .screencapture command, capture a website and send the photo. """
    if SCREENSHOT_LAYER_ACCESS_KEY is None:
        await event.edit(
            "Need to get an API key from https://screenshotlayer.com\
            /product \nModule stopping!")
        return
    await event.edit("Processing ...")
    sample_url = "https://api.screenshotlayer.com/api/capture"
    sample_url += "?access_key={}&url={}&fullpage={}&format={}&viewport={}"
    input_str = event.pattern_match.group(1)
    response_api = get(
        sample_url.format(SCREENSHOT_LAYER_ACCESS_KEY, input_str, "1",
                            "PNG", "2560x1440"),
        stream=True,
    )
    content_type = response_api.headers["content-type"]
    if "image" in content_type:
        temp_file_name = "screencapture.png"
        with open(temp_file_name, "wb") as file:
            for chunk in response_api.iter_content(chunk_size=128):
                file.write(chunk)
        try:
            await event.client.send_file(
                event.chat_id,
                temp_file_name,
                caption=input_str,
                force_document=True,
                reply_to=event.message.reply_to_msg_id,
            )
            await event.delete()
        except BaseException:
            await event.edit(response_api.text)
        os.remove(temp_file_name)
    else:
        await event.edit(response_api.text)


CMD_HELP.update({
    "screencapture":
    ".screencapture <url>"
    "\nUsage: Take a screenshot of a website and send the screenshot."
})
