import typing

import hikari
import tanjun
import lavasnek_rs

component = tanjun.Component()


@component.with_slash_command
@tanjun.as_slash_command("join", "the bot joins the VC you're currently in.")
async def join(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    if channel := await _join_voice(ctx, lavalink):
        await ctx.respond(f"Connected to <#{channel}>")


async def _join_voice(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> typing.Optional[hikari.Snowflake]:
    assert ctx.guild_id is not None

    if ctx.client.cache and ctx.client.shards:
        if not (voice_state := ctx.client.cache.get_voice_state(ctx.guild_id, ctx.author)):
            await ctx.respond(f"Please connect to a voice channel.")
            return None

        channel_id = voice_state.channel_id
        assert channel_id is not None

        await ctx.client.shards.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
        conn = await lavalink.wait_for_full_connection_info_insert(ctx.guild_id)
        await lavalink.create_session(conn)
        return channel_id

    await ctx.respond(f"Unable to join voice. The cache is disabled or the shards are down.")
    return None


@component.with_slash_command()
@tanjun.with_str_slash_option("song", "The title or a youtube link of the song.")
@tanjun.as_slash_command("play", "Plays a song or adds it to the queue.")
async def play(ctx: tanjun.abc.SlashContext, song: str,
               lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink)) -> None:
    await _play_track(ctx, song, lavalink)


async def _play_track(ctx: tanjun.abc.Context, song: str, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    conn = lavalink.get_guild_gateway_connection_info(ctx.guild_id)

    if not conn:
        if not await _join_voice(ctx, lavalink):
            return

    if not (tracks := (await lavalink.auto_search_tracks(song)).tracks):
        await ctx.respond(f"Didn't find any tracks for song: <{song}>")
        return

    try:
        await lavalink.play(ctx.guild_id, tracks[0]).requester(ctx.author.id).queue()
    except lavasnek_rs.NoSessionPresent:
        await ctx.respond(f"Unable to join the voice channel.")
        return

    await ctx.respond(f"Added to queue: `{tracks[0].info.title}`")


@component.with_slash_command
@tanjun.as_slash_command("leave", "Leaves the voice channel and clears the queue.")
async def leave(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _leave_voice(ctx, lavalink)


async def _leave_voice(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    if lavalink.get_guild_gateway_connection_info(ctx.guild_id):
        await lavalink.destroy(ctx.guild_id)

        if ctx.client.shards:
            await ctx.client.shards.update_voice_state(ctx.guild_id, None)
            await lavalink.wait_for_connection_info_remove(ctx.guild_id)

        await lavalink.remove_guild_node(ctx.guild_id)
        await lavalink.remove_guild_from_loops(ctx.guild_id)

        await ctx.respond(f"Disconnected from voice channel.")
        return

    await ctx.respond(f"I'm currently not connected")


@component.with_slash_command
@tanjun.as_slash_command("stop", "Stops the currently playing song, skip to play again.")
async def stop(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _stop_playback(ctx, lavalink)


async def _stop_playback(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    await lavalink.stop(ctx.guild_id)
    await ctx.respond(f"Stopped the playback.")


@component.with_slash_command
@tanjun.as_slash_command("skip", "Skips the current song.")
async def skip(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _skip_track(ctx, lavalink)


async def _skip_track(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    if not (skip := await lavalink.skip(ctx.guild_id)):
        await ctx.respond(f"No tracks left to skip.")
        return

    elif node := await lavalink.get_guild_node(ctx.guild_id):
        if not node.queue and node.now_playing:
            await lavalink.stop(ctx.guild_id)

    await ctx.respond(f"Skipped: {skip.track.info.title}")


@component.with_slash_command
@tanjun.as_slash_command("pause", "Pauses the current song.")
async def pause(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _pause_playback(ctx, lavalink)


async def _pause_playback(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    await lavalink.pause(ctx.guild_id)
    await ctx.respond("Paused the playback.")


@component.with_slash_command
@tanjun.as_slash_command("resume", "Resumes the current song.")
async def resume(
        ctx: tanjun.abc.SlashContext,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _resume_playback(ctx, lavalink)


async def _resume_playback(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    await lavalink.resume(ctx.guild_id)
    await ctx.respond("Resuming playback.")


@component.with_slash_command
@tanjun.as_slash_command("playing", "Displays info on the currently playing song.")
async def playing(
        ctx: tanjun.abc.Context,
        lavalink: lavasnek_rs.Lavalink = tanjun.injected(type=lavasnek_rs.Lavalink),
) -> None:
    await _playing(ctx, lavalink)


async def _playing(ctx: tanjun.abc.Context, lavalink: lavasnek_rs.Lavalink) -> None:
    assert ctx.guild_id is not None

    if not (node := await lavalink.get_guild_node(ctx.guild_id)):
        await ctx.respond("Unable to connect to the node.")
        return

    if not node.now_playing:
        await ctx.respond("Nothing is playing now.")
        return

    if node.now_playing:
        await ctx.respond(
            f"Title: {node.now_playing.track.info.title}\n" f"Requested by: <@!{node.queue[0].requester}>"
        )


@tanjun.as_loader
def load(client: tanjun.abc.Client) -> None:
    client.add_component(component.copy())
