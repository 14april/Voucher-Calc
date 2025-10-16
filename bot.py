import os
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

# ====== Cấu hình intents ======
intents = discord.Intents.default()
intents.message_content = True

# ====== Tạo bot ======
bot = commands.Bot(command_prefix="!", intents=intents)

# ====== Khi bot sẵn sàng ======
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập thành công: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Đã đồng bộ {len(synced)} lệnh slash.")
    except Exception as e:
        print(f"❌ Lỗi sync command: {e}")

# ====== Slash command /calc ======
@bot.tree.command(name="calc", description="Tính số vé trong tương lai 📅")
async def calc(interaction: discord.Interaction):
    # Tạo 2 nút chọn
    class TicketSelect(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Vé đen", style=discord.ButtonStyle.primary, emoji="<:bt:1378705629182562304>")
        async def black_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await ask_current_ticket(interaction, "đen")

        @discord.ui.button(label="Vé kỉ vật", style=discord.ButtonStyle.success, emoji="<:ks:1378705636396892330>")
        async def relic_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await ask_current_ticket(interaction, "kỉ vật")

    await interaction.response.send_message("🎯 Chọn loại vé bạn muốn tính:", view=TicketSelect(), ephemeral=True)

# ====== Hỏi số vé hiện tại & số tháng cần tính ======
async def ask_current_ticket(interaction: discord.Interaction, ticket_type: str):
    await interaction.response.send_message(f"🧮 Nhập **số vé {ticket_type} hiện tại** của bạn:", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    msg = await bot.wait_for("message", check=check)
    try:
        current_ticket = int(msg.content)
    except ValueError:
        await interaction.followup.send("⚠️ Vui lòng nhập số hợp lệ.", ephemeral=True)
        return

    await interaction.followup.send("📆 Nhập **số tháng cần tính (1–12)**:", ephemeral=True)
    msg2 = await bot.wait_for("message", check=check)
    try:
        months = int(msg2.content)
        if not (1 <= months <= 12):
            raise ValueError
    except ValueError:
        await interaction.followup.send("⚠️ Số tháng phải từ 1 đến 12.", ephemeral=True)
        return

    # ====== Tính kết quả với tháng/năm thực ======
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    per_month = 81 if ticket_type == "đen" else 18

    results = []
    ticket = current_ticket

    for i in range(1, months + 1):
        next_month = current_month + i
        next_year = current_year
        if next_month > 12:
            next_month -= 12
            next_year += 1

        ticket += per_month
        results.append(f"📅 **Tháng {next_month}/{next_year}:** {ticket} vé {ticket_type}")

    # Hiển thị kết quả
    await interaction.followup.send(
        f"✅ **Kết quả dự tính cho vé {ticket_type}:**\n" + "\n".join(results),
        ephemeral=True
    )

# ====== Chạy bot ======
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("⚠️ Chưa có biến môi trường DISCORD_TOKEN!")
else:
    bot.run(TOKEN)
