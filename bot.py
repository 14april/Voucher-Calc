import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

# ----- Config -----
TOKEN = "MTQyODMxMjUzMzc4MTE4NDUxMg.GWiSvX.yYBMM9Sy1CgW9Z4juZF3KNdrvtBhYaeyccSJMM"
black_ticket = 81
relic_ticket = 18

# ------------------

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

@bot.tree.command(name="calc", description="Tính số vé trong tương lai")
async def calc(interaction: discord.Interaction):
    # Gửi 2 nút chọn loại vé
    view = TicketTypeView()
    await interaction.response.send_message("Chọn loại vé bạn muốn tính:", view=view, ephemeral=True)


class TicketTypeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎟️ Vé đen", style=discord.ButtonStyle.primary)
    async def black_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Nhập số vé hiện tại của bạn:", ephemeral=True)
        bot.ticket_type[interaction.user.id] = "black"

    @discord.ui.button(label="🧭 Vé kỉ vật", style=discord.ButtonStyle.secondary)
    async def relic_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Nhập số vé hiện tại của bạn:", ephemeral=True)
        bot.ticket_type[interaction.user.id] = "relic"


bot.ticket_type = {}
bot.user_stage = {}
bot.ticket_value = {}

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    uid = message.author.id

    # Kiểm tra xem người này đang nhập số vé không
    if uid in bot.ticket_type and uid not in bot.user_stage:
        try:
            current_ticket = int(message.content)
            bot.ticket_value[uid] = current_ticket
            bot.user_stage[uid] = "waiting_months"
            await message.reply("Nhập số **tháng** bạn muốn tính (1-12):")
        except ValueError:
            await message.reply("⚠️ Hãy nhập số hợp lệ.")

    elif uid in bot.user_stage and bot.user_stage[uid] == "waiting_months":
        try:
            months = int(message.content)
            if months < 1 or months > 12:
                await message.reply("⚠️ Nhập từ 1 đến 12 thôi nha.")
                return

            now = datetime.now()
            ticket_type = bot.ticket_type[uid]
            base = black_ticket if ticket_type == "black" else relic_ticket

            result = []
            total = bot.ticket_value[uid]
            for i in range(1, months + 1):
                month = (now.month + i - 1) % 12 + 1
                total += base
                result.append(f"📅 Tháng {month}: +{base} → **{total}** { 'vé đen' if ticket_type=='black' else 'vé kỉ vật' }")

            await message.reply("\n".join(result))
            # Xóa dữ liệu tạm
            bot.ticket_type.pop(uid, None)
            bot.user_stage.pop(uid, None)
            bot.ticket_value.pop(uid, None)

        except ValueError:
            await message.reply("⚠️ Hãy nhập số hợp lệ.")


bot.run(TOKEN)
