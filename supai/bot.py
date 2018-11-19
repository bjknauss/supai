from dynaconf import settings
import discord
import aiohttp
from supai import target
from typing import List
import io

class Supai(discord.Client):
    '''Supai is a Discord logging bot that uses webhooks to log channel activity.'''

    def __init__(self, *args, **kwargs):
        kwargs["fetch_offline_members"] = True
        super().__init__(*args, **kwargs)
        self.targets: List[target.Target] = []


    def init_targets(self):
        targets = []
        for t in settings.TARGETS:
            print(t)
            print(type(t))
            channel = self.get_channel(t['channel'])
            targ = target.Target(name=t['name'], channel=channel, webhook=t['webhook'])
            print(f'Target: {targ}')
            targets.append(targ)

        self.targets = targets

    async def spy_message(self, target: target.Target, msg: discord.Message):
        '''Sends the message to the webhook mimicking the original message as close as possible. Includes message content, embeds, and files.'''
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(target.webhook, adapter=discord.AsyncWebhookAdapter(session))
            if len(msg.content) > 0 or len(msg.embeds) > 0:
                await webhook.send(content=msg.content, username=str(msg.author), avatar_url=msg.author.avatar_url, embeds=msg.embeds)
            for attach in msg.attachments:
                fp = io.BytesIO()
                await attach.save(fp)
                attach_file = discord.File(fp, filename=attach.filename)
                await webhook.send(username=str(msg.author), file=attach_file, avatar_url=msg.author.avatar_url)
                fp.close()


    def run(self):
        token = settings.TOKEN
        super().run(token)


    async def on_ready(self):
        self.init_targets()
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        '''Checks to see if message is from one of our target channels.'''
        for target in self.targets:
            if message.channel == target.channel:
                await self.spy_message(target, message)
