from typing import NamedTuple
import discord

class TargetSetting(NamedTuple):
    '''Represents a target in the dynaconf settings.'''
    name: str
    channel: int
    webhook: str


class Target(NamedTuple):
    '''Fully initialized target to spy on.'''
    name: str
    channel: discord.TextChannel
    webhook: str
