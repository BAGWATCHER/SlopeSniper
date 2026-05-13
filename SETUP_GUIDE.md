# Complete Setup Guide: SlopeSniper + Moltbot

> **For complete beginners** - No coding knowledge required!

This guide walks you through setting up SlopeSniper with Moltbot from scratch. Follow these steps in order.

---

## What You're Setting Up

**Moltbot** = Your AI assistant that runs on your computer and connects to messaging apps
**SlopeSniper** = The trading skill that lets Moltbot trade Solana tokens for you

Think of it like: Moltbot is your phone, SlopeSniper is an app you install on it.

---

## Part 1: Install Moltbot (15-20 minutes)

### Step 1: Install Moltbot

**Mac/Linux:**
```bash
curl -fsSL https://molt.bot/install.sh | bash
```

**Windows (PowerShell as Admin):**
```powershell
iwr -useb https://molt.bot/install.ps1 | iex
```

✅ **You'll know it worked when:** You see "Installation complete!"

❌ **If it fails:** Make sure you have Node.js 22+ installed. [Get it here](https://nodejs.org/)

---

### Step 2: Run the Setup Wizard

```bash
moltbot onboard --install-daemon
```

This wizard will ask you questions. Here's what to choose:

#### Question 1: "Local or Remote gateway?"
**Choose:** `Local` (unless you know you need remote)

#### Question 2: "Which AI provider?"
**Choose:** One of these:
- **OpenAI** - Need API key from [platform.openai.com](https://platform.openai.com/api-keys)
- **Anthropic** - Need API key from [console.anthropic.com](https://console.anthropic.com/)

💡 **Tip:** Start with OpenAI if you're unsure (most common)

#### Question 3: "Which messaging platform?"
**Choose:** 
- **WhatsApp** (easiest - just scan QR code)
- **Telegram** (requires setting up a bot)
- **Discord** (requires bot setup)

We recommend WhatsApp for beginners.

#### Question 4: "Install as background service?"
**Choose:** `Yes` (this lets Moltbot run automatically)

---

### Step 3: Start Moltbot

```bash
moltbot gateway status
```

✅ **Should say:** "Gateway is running"

If not running, start it:
```bash
moltbot gateway --port 18789
```

---

### Step 4: Connect Your Messaging App

**For WhatsApp:**
```bash
moltbot channels login
```
Then scan the QR code with WhatsApp on your phone (like WhatsApp Web).

**For Telegram:**
Follow the [Telegram setup guide](https://docs.molt.bot/channels/telegram)

✅ **You'll know it worked when:** You can message your bot and it responds!

**Try sending:** "Hello!"

---

## Part 2: Install SlopeSniper (5 minutes)

Now that Moltbot is running, let's add the trading skill.

### Step 1: Install SlopeSniper

```bash
curl -fsSL https://raw.githubusercontent.com/optimizedwf/SlopeSniper/main/skills/install.sh | bash
```

✅ **You'll know it worked when:** You see "Installation complete!"

---

### Step 2: Set Up Your Trading Wallet

**IMPORTANT:** This creates a NEW wallet just for trading. Don't use your main wallet!

```bash
slopesniper setup
```

The wizard will:
1. Create a new wallet
2. Show you the **private key** (SAVE THIS!)
3. Ask you to confirm you saved it
4. Give you a wallet address

📋 **Write down your private key RIGHT NOW:**
- Save it in a password manager (1Password, Bitwarden, etc.)
- Write it on paper and put it somewhere safe
- **If you lose this, your funds are gone forever**

---

### Step 3: Fund Your Wallet

1. **Copy your wallet address** from the setup output
2. **Send SOL** to this address from your main wallet
   - Start small: 0.1-0.5 SOL is enough to test
3. **Wait 30 seconds** for the transaction to confirm

Check your balance:
```bash
slopesniper status
```

✅ **Should show:** Your SOL balance

---

## Part 3: Make Your First Trade (2 minutes)

Now message your Moltbot! Try these commands:

### Check Everything Works
**You:** `check my status`
**Bot:** Shows your wallet address, SOL balance, and trading strategy

### Get a Token Price
**You:** `What's the price of SOL?`
**Bot:** Shows current SOL price in USD

### Make a Small Test Trade
**You:** `Buy $5 of BONK`
**Bot:** Will find BONK, run safety checks, get a quote, and execute the trade

✅ **If it works:** Congrats! You're trading with AI! 🎉

---

## Common Problems & Fixes

### "Command not found: moltbot"
**Fix:** Close and reopen your terminal, or add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### "Command not found: slopesniper"
**Fix:** The installation didn't complete. Try manually:
```bash
curl -fsSL https://astral.sh/uv/install.sh | sh
uv tool install "slopesniper-mcp @ git+https://github.com/optimizedwf/SlopeSniper.git#subdirectory=mcp-extension"
```

### "Gateway is not running"
**Fix:**
```bash
moltbot gateway --port 18789
```
Leave this terminal open and open a new one for other commands.

### "Transaction failed: slippage"
**Fix:** Increase slippage tolerance:
```bash
slopesniper strategy --slippage 300
```
(This sets 3% slippage instead of default 1%)

### "Insufficient funds"
**Fix:** You need more SOL. Each trade needs:
- Trade amount (e.g., $5)
- Gas fees (~$0.01 per transaction)

### Bot doesn't respond in WhatsApp/Telegram
**Fix:** 
1. Check gateway is running: `moltbot gateway status`
2. Check channel is connected: `moltbot status`
3. Restart gateway: `moltbot gateway restart`

---

## Next Steps

🎓 **Learn the commands:**
- Read [SKILL.md](https://github.com/optimizedwf/SlopeSniper/blob/main/skills/slopesniper/SKILL.md)
- All commands work via natural language

⚙️ **Customize your strategy:**
```bash
slopesniper strategy aggressive    # Higher limits
slopesniper strategy conservative  # Lower limits
```

🔒 **Back up your wallet:**
```bash
slopesniper export
```
Save this output somewhere safe!

📊 **Track your performance:**
```bash
slopesniper pnl        # Profit/loss
slopesniper history    # Recent trades
```

---

## Safety Tips

1. ✅ **Use a separate wallet** - Never import your main wallet
2. ✅ **Start small** - Test with $5-10 trades first
3. ✅ **Back up your key** - Do this TODAY, not tomorrow
4. ✅ **Understand the risks** - Crypto is volatile, meme coins especially
5. ✅ **Check safety scores** - SlopeSniper runs rugcheck before every trade

---

## Get Help

- **GitHub Issues:** [github.com/optimizedwf/SlopeSniper/issues](https://github.com/optimizedwf/SlopeSniper/issues)
- **Official Docs:** [github.com/optimizedwf/SlopeSniper](https://github.com/optimizedwf/SlopeSniper)

---

**Ready to trade?** Head to your Moltbot chat and say: `check my status` 🚀
