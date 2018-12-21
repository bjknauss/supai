from dynaconf import settings
import discord
import aiohttp
from supai import target
from typing import List
import io
from datetime import datetime

class Supai(discord.Client):
    '''Supai is a Discord logging bot that uses webhooks to log channel activity.'''

    def __init__(self, *args, **kwargs):
        kwargs["fetch_offline_members"] = True
        super().__init__(*args, **kwargs)
        self.targets: List[target.Target] = []
        self.targets_initialized = False


    def init_targets(self):
        targets = []
        if self.targets_initialized:
            print(f'Targets have already been initialized... ')
            print(datetime.now())
        else:
            print('Initializing Targets...')
        for t in settings.TARGETS:
            print(t)
            print(type(t))
            channel = self.get_channel(t['channel'])
            targ = target.Target(name=t['name'], channel=channel, webhook=t['webhook'])
            print(f'Target: {targ}')
            targets.append(targ)

        self.targets = targets
        self.targets_initialized = True

    def mentions_embed(self, msg: discord.Message) -> discord.Embed:
        '''Builds an Embed object for mentions which includes the display name and user id of the mentions. '''
        mentions = msg.mentions[:24]
        if len(mentions):
            embed = discord.Embed()
            for mention in mentions:
                name = f'{mention.name}#{mention.discriminator}'
                value = str(mention.id)
                if(mention.name != mention.display_name):
                    value += f'\n@{mention.display_name}'
                embed.add_field(name=name, value=value, inline=True)
            return embed
        return None

    async def spy_message(self, target: target.Target, msg: discord.Message):
        '''Sends the message to the webhook mimicking the original message as close as possible. Includes message content, embeds, and files.'''
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(target.webhook, adapter=discord.AsyncWebhookAdapter(session))
            name = str(msg.author.name)
            if len(name) < 3:
                print(f'MESSAGE AUTHOR TOO SHORT... {name}')
                print(msg)

            if len(name) > 32:
                print(f'MESSAGE AUTHOR TOO LONG... {name}')
                print(msg)

            if len(msg.content) or len(msg.embeds):
                content=msg.clean_content if msg.mention_everyone else msg.content
                mention_embed = self.mentions_embed(msg)
                if mention_embed:
                    msg.embeds.append(mention_embed)
                await webhook.send(content=content, username=name, avatar_url=msg.author.avatar_url, embeds=msg.embeds)
            for attach in msg.attachments:
                fp = io.BytesIO()
                await attach.save(fp)
                attach_file = discord.File(fp, filename=attach.filename)
                await webhook.send(username=name, file=attach_file, avatar_url=msg.author.avatar_url)
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
