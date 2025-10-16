import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import discord
from discord import app_commands
from discord.ext import commands

# ====== Fake web server để Render không kill ======
class PingServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), PingServer)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()


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


# ====== Hàm xử lý tính vé ======
async def calculate_tickets(interaction: discord.Interaction, ticket_type: str, current_ticket: int, months: int):
    per_month = 81 if ticket_type == "đen" else 18
    results = []
    for i in range(1, months + 1):
        total = current_ticket + per_month * i
        results.append(f"Tháng {i}: **{total} vé {ticket_type}**")

    await interaction.followup.send(
        f"📊 Kết quả dự tính cho **{ticket_type}**:\n" + "\n".join(results),
        ephemeral=True
    )


# ====== Modal nhập dữ liệu ======
class TicketModal(discord.ui.Modal, title="Tính vé trong tương lai"):
    def __init__(self, ticket_type):
        super().__init__()
        self.ticket_type = ticket_type

        self.current_ticket = discord.ui.TextInput(
            label=f"Số vé {ticket_type} hiện tại",
            placeholder="Nhập số vé (vd: 100)",
            required=True,
        )
        self.months = discord.ui.TextInput(
            label="Số tháng muốn tính (1–12)",
            placeholder="Nhập số tháng (vd: 3)",
            required=True,
        )

        self.add_item(self.current_ticket)
        self.add_item(self.months)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            current_ticket = int(self.current_ticket.value)
            months = int(self.months.value)
            if not (1 <= months <= 12):
                raise ValueError
        except ValueError:
            await interaction.response.send_message("⚠️ Dữ liệu không hợp lệ.", ephemeral=True)
            return

        # defer để tránh Unknown interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        await calculate_tickets(interaction, self.ticket_type, current_ticket, months)


# ====== Fallback hỏi qua chat ======
async def fallback_chat(interaction: discord.Interaction, ticket_type: str):
    await interaction.response.send_message(f"Nhập **Số vé {ticket_type} hiện tại**:", ephemeral=True)

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        msg1 = await bot.wait_for("message", check=check, timeout=60)
        current_ticket = int(msg1.content)
    except:
        await interaction.followup.send("⚠️ Dữ liệu không hợp lệ hoặc hết thời gian nhập.", ephemeral=True)
        return

    await interaction.followup.send("Nhập **Số tháng cần tính (1–12)**:", ephemeral=True)
    try:
        msg2 = await bot.wait_for("message", check=check, timeout=60)
        months = int(msg2.content)
        if not (1 <= months <= 12):
            raise ValueError
    except:
        await interaction.followup.send("⚠️ Dữ liệu không hợp lệ hoặc hết thời gian nhập.", ephemeral=True)
        return

    await calculate_tickets(interaction, ticket_type, current_ticket, months)

    # Xóa tin nhắn người dùng để "ẩn log"
    try:
        await msg1.delete()
        await msg2.delete()
    except:
        pass


# ====== Lệnh /calc ======
@bot.tree.command(name="calc", description="Tính số vé trong tương lai 📅")
async def calc(interaction: discord.Interaction):
    await interaction.response.defer(thinking=False, ephemeral=True)

    class TicketSelect(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Vé đen", style=discord.ButtonStyle.primary, emoji="<:bt:1378705629182562304>")
        async def black_ticket(self, i: discord.Interaction, button: discord.ui.Button):
            try:
                await i.response.send_modal(TicketModal("đen"))
            except:
                await fallback_chat(i, "đen")

        @discord.ui.button(label="Vé kỉ vật", style=discord.ButtonStyle.success, emoji="<:ks:1378705636396892330>")
        async def relic_ticket(self, i: discord.Interaction, button: discord.ui.Button):
            try:
                await i.response.send_modal(TicketModal("kỉ vật"))
            except:
                await fallback_chat(i, "kỉ vật")

    await interaction.followup.send("🎫 Chọn loại vé bạn muốn tính:", view=TicketSelect(), ephemeral=True)


# ====== Chạy bot ======
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("⚠️ Chưa có biến môi trường DISCORD_TOKEN!")
else:
    bot.run(TOKEN)

