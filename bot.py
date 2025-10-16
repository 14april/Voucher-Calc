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

# ====== Modal nhập thông tin ======
class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        super().__init__(title="📋 Nhập thông tin tính vé")
        self.ticket_type = ticket_type

        # Ô nhập số vé hiện tại
        self.current_ticket = discord.ui.TextInput(
            label=f"Số vé {ticket_type} hiện tại",
            placeholder="vd: 20",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )

        # Ô nhập số tháng cần tính
        self.months = discord.ui.TextInput(
            label="Số tháng cần tính (1–12)",
            placeholder="vd: 4",
            style=discord.TextStyle.short,
            required=True,
            max_length=2
        )

        self.add_item(self.current_ticket)
        self.add_item(self.months)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            current_ticket = int(self.current_ticket.value.strip())
            months = int(self.months.value.strip())
            if not (1 <= months <= 12):
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "⚠️ Vui lòng nhập số hợp lệ (vé là số nguyên, tháng từ 1–12).",
                ephemeral=True
            )
            return

        # ====== Tính toán ======
        now = datetime.now()
        current_month = now.month
        current_year = now.year

        per_month = 81 if self.ticket_type == "đen" else 18
        ticket = current_ticket
        results = []

        for i in range(1, months + 1):
            next_month = current_month + i
            next_year = current_year
            if next_month > 12:
                next_month -= 12
                next_year += 1

            ticket += per_month
            results.append(f"📅 **Tháng {next_month}/{next_year}:** {ticket} vé {self.ticket_type}")

        # ====== Gửi kết quả ======
        embed = discord.Embed(
            title=f"📊 Dự tính vé {self.ticket_type}",
            description="\n".join(results),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Tính từ tháng {current_month}/{current_year}")

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ====== Giao diện chọn loại vé ======
class TicketSelect(discord.ui.View):
    @discord.ui.button(label="Vé đen", style=discord.ButtonStyle.primary, emoji="<:bt:1378705629182562304>")
    async def black_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal("đen"))

    @discord.ui.button(label="Vé kỉ vật", style=discord.ButtonStyle.success, emoji="<:ks:1378705636396892330>")
    async def relic_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal("kỉ vật"))

# ====== Slash command /calc ======
@bot.tree.command(name="calc", description="Tính số vé trong tương lai 📅")
async def calc(interaction: discord.Interaction):
    await interaction.response.send_message("🎯 Chọn loại vé bạn muốn tính:", view=TicketSelect(), ephemeral=True)

# ====== Chạy bot ======
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("⚠️ Chưa có biến môi trường DISCORD_TOKEN!")
else:
    bot.run(TOKEN)
