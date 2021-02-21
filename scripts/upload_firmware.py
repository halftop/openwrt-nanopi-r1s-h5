#!/usr/bin/env python3
#-*-coding:utf-8-*-

from pyrogram import Client

import argparse
import logging
import os
import re
import subprocess
import time

logging.basicConfig(level=logging.WARN)

''' init arguments start '''
parser = argparse.ArgumentParser()
parser.add_argument("--device-name", help="The nickname of supported device", type=str, required=True)
parser.add_argument("--device-file", help="The filename of supported device", type=str, required=True)
parser.add_argument("--openwrt-version", help="OpenWrt version of firmware", type=str, required=True)
parser.add_argument("--kernel-version", help="Kernel version of firmware", type=str, required=True)
parser.add_argument("--api-id", help="Telegram Application ID", type=str, required=True)
parser.add_argument("--api-hash", help="Telegram Application HASH", type=str, required=True)
parser.add_argument("--bot-token", help="Telegram Bot Token", type=str, required=True)
args = parser.parse_args()

base_dir = "/home/runner"
post_channel = "@nanopi_r2s"
release_date = time.strftime("%Y-%m-%d %H:%M %z", time.localtime())
''' init arguments end '''

''' check if files exist start'''
try:
	sha256sums_file = open("%s/openwrt-%s-sha256sums" % (base_dir, args.openwrt_version))
	sha256sums_file.close()
except IOError:
	print("OpenWrt Firmware is not accessible.")
	exit(1)
''' check if files exist end '''

''' init telegram bot start '''
bot = Client('bot', bot_token=args.bot_token, api_id=args.api_id, api_hash=args.api_hash)
bot.start()
''' init telegram bot end '''

''' def basic functions start '''
def grep(context, keyword):
	text = []
	for line in context:
		if keyword in line:
			text.append(line)
	if text:
		return text
	else:
		return [ "False" ]

def get_firmware_hash(format):
	sha256sums_file = open("%s/openwrt-%s-sha256sums" % (base_dir, args.openwrt_version), "r", encoding="utf-8")
	sha256sum_info = grep(sha256sums_file.readlines(), "openwrt-%s-%s-sdcard.img.gz" % (args.device_file, format))[0]
	sha256sum = sha256sum_info.split(" ")[0]
	sha256sums_file.close()
	if sha256sum:
		return sha256sum
	else:
		return "False"

def transfer_upload(host_provider, format):
	file_name = "openwrt-%s-%s-%s-sdcard.img.gz" % (args.openwrt_version, args.device_file, format)
	if host_provider == "wet":
		download_link_info = subprocess.getoutput("%s/transfer --no-progress 'wet' -s -p '16' -t '180' '%s/%s' \
						| grep 'Download Link' | grep -v 'grep'" % (base_dir, base_dir, file_name))
	else:
		download_link_info = subprocess.getoutput("%s/transfer --no-progress '%s' '%s/%s' | grep 'Download Link' \
							| grep -v 'grep'" % (base_dir, host_provider, base_dir, file_name))
	download_link = download_link_info.split(": ")[1]
	if download_link:
		return download_link
	else:
		return "False"
''' def basic functions end '''

''' init firmware info start '''
ext4_image_hash = get_firmware_hash("ext4")
squashfs_image_hash = get_firmware_hash("squashfs")
firmware_sha256sum_message = "EXT4 Firmware:\n`%s`\nSquashFS Firmware:\n`%s`" % (ext4_image_hash, squashfs_image_hash)
''' init firmware info end '''

''' upload firmware to cloud start '''
os.system("cd '%s'; curl -sL 'https://git.io/file-transfer' | sh" % base_dir)
try:
	transfer_file = open("%s/transfer" % base_dir)
	transfer_file.close()
	transfer_disable = False
except IOError:
	print("Transfer is not accessible.")
	transfer_disable = True

if not transfer_disable:
	cat_ext4_download_link = transfer_upload("cat", "ext4")
	wet_ext4_download_link = transfer_upload("wet", "ext4")

	cat_squashfs_download_link = transfer_upload("cat", "squashfs")
	wet_squashfs_download_link = transfer_upload("wet", "squashfs")

	firmware_download_link_message = "EXT4 Firmware:\n%s\n%s\n" % (cat_ext4_download_link, wet_ext4_download_link)
	firmware_download_link_message += "SquashFS Firmware:\n%s\n%s"  % (cat_squashfs_download_link, wet_squashfs_download_link)
''' upload firmware to cloud end '''

''' send message to telegram start '''
pending_message = "**Release Date: %s**\n**Supported Device: %s**\n" % (release_date, args.device_name)
pending_message += "**OpenWrt Version: %s**\n**Kernel Version: %s**\n\n" % (args.openwrt_version, args.kernel_version)
pending_message += "SHA256SUM Hash\n%s" % firmware_sha256sum_message
if not transfer_disable:
	pending_message += "\n\nDownload Link\n%s" % firmware_download_link_message

bot.send_document(post_channel, document="%s/openwrt-%s-%s-sdcard.zip" % (base_dir, args.openwrt_version,
									args.device_file), caption=pending_message)
bot.stop()
''' send message to telegram end '''
