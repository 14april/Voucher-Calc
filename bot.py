import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime # Thêm import datetime để lấy ngày hiện tại

# ====== Fake web server để Render không kill ======
class PingServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_server():
    # Sử dụng '0.0.0.0' để lắng nghe trên mọi giao diện mạng,
    # và lấy port từ biến môi trường.
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


# ====== Hàm xử lý tính vé đã được FIX ======
async def calculate_tickets(interaction: discord.Interaction, ticket_type: str, current_ticket: int, months: int):
    # Lấy ngày hiện tại để tính toán tháng và năm bắt đầu
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    per_month = 81 if ticket_type == "đen" else 18
    results = []
    
    # Duyệt qua số tháng mà người dùng muốn tính
    for i in range(1, months + 1):
        total = current_ticket + per_month * i
        
        # Tính tháng và năm trong tương lai
        # target_month_raw là tổng số tháng trôi qua kể từ đầu năm hiện tại
        target_month_raw = current_month + i
        
        # Tính năm: Tăng năm nếu vượt qua 12 tháng (vd: 13 tháng -> tăng 1 năm)
        # Lấy phần nguyên của (tổng số tháng - 1) / 12
        target_year = current_year + (target_month_raw - 1) // 12
        
        # Tính tháng: Lấy tháng từ 1-12
        # Lấy phần dư của (tổng số tháng - 1) chia 12, sau đó cộng 1
        target_month = (target_month_raw - 1) % 12 + 1
        
        # Định dạng kết quả tháng/năm
        month_str = f"**{target_month}/{target_year}**"
        
        # Cập nhật kết quả với tháng/năm đã tính
        results.append(f"{month_str}: **{total} vé {ticket_type}**")

    await interaction.followup.send(
        f"📊 Kết quả dự tính cho **{ticket_type}** (Tính từ tháng sau):\n" + "\n".join(results),
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
            await interaction.response.send_message("⚠️ Dữ liệu không hợp lệ. Vui lòng kiểm tra lại số vé và số tháng (1-12).", ephemeral=True)
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

    # Defer interaction before calling calculate_tickets to avoid the dreaded "Unknown interaction"
    await interaction.channel.send("Đang tính toán...", delete_after=0.5)
    await calculate_tickets(interaction, ticket_type, current_ticket, months)

    # Xóa tin nhắn người dùng để "ẩn log"
    try:
        # Xóa tin nhắn defer tạm thời của bot
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
                # Nếu interaction chưa được response, dùng response.send_modal
                await i.response.send_modal(TicketModal("đen"))
            except discord.errors.InteractionResponded:
                # Nếu đã được response (trong trường hợp fallback), thì không làm gì cả
                pass
            except:
                # Nếu xảy ra lỗi khác (ví dụ: modal hết hạn), dùng fallback
                await fallback_chat(i, "đen")

        @discord.ui.button(label="Vé kỉ vật", style=discord.ButtonStyle.success, emoji="<:ks:1378705636396892330>")
        async def relic_ticket(self, i: discord.Interaction, button: discord.ui.Button):
            try:
                await i.response.send_modal(TicketModal("kỉ vật"))
            except discord.errors.InteractionResponded:
                pass
            except:
                await fallback_chat(i, "kỉ vật")

    await interaction.followup.send("🎫 Chọn loại vé bạn muốn tính:", view=TicketSelect(), ephemeral=True)


# ====== Chạy bot ======
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("⚠️ Chưa có biến môi trường DISCORD_TOKEN!")
else:
    bot.run(TOKEN)
