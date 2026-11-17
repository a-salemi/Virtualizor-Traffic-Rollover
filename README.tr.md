# ⚡ VirtuRoll (Virtualizor Trafik Devir ve Yönetim Sistemi)

<p align="center">
  <img src="https://img.shields.io/badge/VirtuRoll-Sürüm%202.0.0-6366f1?style=for-the-badge&logo=fastapi&logoColor=white" alt="VirtuRoll Version" />
  <img src="https://img.shields.io/badge/Virtualizor-API%204085-06b6d4?style=for-the-badge&logo=linux&logoColor=white" alt="Virtualizor" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Telegram-Bot%20Bildirimleri-229ed9?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/Lisans-MIT-emerald?style=for-the-badge" alt="License MIT" />
</p>

<p align="center">
  <b>Virtualizor sanallaştırma düğümleri için kurumsal düzeyde otomatik trafik devir (Rollover) ve çoklu sunucu yönetim motoru.</b><br>
  <i>Ön ödemeli VPS paketlerinde her ay başı yaşanan bant genişliği sıfırlanma kayıplarını tamamen engeller. %100 Yerel (Docker Gerektirmez).</i>
</p>

<p align="center">
  <b>🌐 Diğer Diller / Other Languages:</b><br>
  <a href="README.md"><b>English</b></a> •
  <a href="README.fa.md"><b>فارسی (Persian)</b></a> •
  <a href="README.ru.md"><b>Русский (Russian)</b></a> •
  <a href="README.zh.md"><b>简体中文 (Chinese)</b></a> •
  <a href="README.tr.md"><b>Türkçe (Turkish)</b></a> •
  <a href="README.ar.md"><b>العربية (Arabic)</b></a>
</p>

---

## 📖 İçindekiler
- [Karşılaşılan Sorun](#-karşılaşılan-sorun)
- [VirtuRoll Çözümü](#-virturoll-çözümü)
- [Temel Özellikler](#-temel-özellikler)
- [Tek Komutla Kolay Kurulum](#-tek-komutla-kolay-kurulum-ubuntu--debian)
- [Hızlı Güncelleme](#-hızlı-güncelleme)
- [Virtualizor Panel Bağlantı Rehberi](#-virtualizor-panel-bağlantı-rehberi)
- [Telegram Bildirimleri ve Yedekleme](#-telegram-bildirimleri-ve-yedekleme)
- [Servis Yönetimi](#-servis-yönetimi)
- [Lisans](#-lisans)

---

## 🛑 Karşılaşılan Sorun

**Virtualizor**, varsayılan olarak tüm bant genişliklerini aylık tekrarlayan abonelikler şeklinde yönetir. Her takvim ayının 1'inde saat 00:00'da:
1. Virtualizor tüm sanal sunucuların kullanılan bant genişliği (`used_bandwidth`) sayacını **`0 GB`** olarak sıfırlar.
2. Müşteri **5 TB ön ödemeli paket** almış ve 4 TB kullanmışsa, ayın 1'inde kalan 1 TB hakkı yerine sıfırdan 5 TB yeni kota tanımlanır.
3. Bu durum sunucu sağlayıcıları açısından ciddi bant genişliği kaçaklarına ve gelir kaybına neden olur.

---

## ✨ VirtuRoll Çözümü

**VirtuRoll**, Virtualizor hipervizörünü tek ve kesin gerçeklik kaynağı kabul ederek arka planda bir sistem servisi olarak çalışır:

$$\text{Gerçek Kalan Bant Genişliği} = \text{Düğüm Kotası} - \text{Bu Dönem Tüketilen}$$

Ay başı sıfırlama olayı tetiklendiğinde (kullanımın aniden düşmesiyle otomatik algılanır), VirtuRoll:
1. Her sanal sunucunun gerçek kalan trafik bakiyesini hesaplar.
2. Virtualizor Admin API'si üzerinden (`POST /index.php?act=editvs`) sunucunun limitini tam kalan miktar olarak günceller.
3. Limitsiz sunucuları (`bandwidth = 0`) güvenle hariç tutar.
4. Olayı denetim günlüğüne işler ve **Telegram Botunuza** anında bildirim gönderir.

---

## 🌟 Temel Özellikler

| Yetenek | Açıklama |
| :--- | :--- |
| 🔄 **Olay Güdümlü Devir Motoru** | Zaman dilimlerine veya sabit cron görevlerine bağımlı olmadan sıfırlamayı yakalar ve trafiği devreder. |
| 🎛️ **Çoklu Panel Yönetimi** | Özel **Paneller** sekmesi üzerinden sınırsız Virtualizor ana ve alt düğümünü ekleyin, düzenleyin ve test edin. |
| 📊 **Sunucu Donanım Telemetrisi** | Ani sıçrama yapmayan pürüzsüz CPU kullanımı, RAM, SWAP, disk ve çalışma süresini izleyin. |
| 🤖 **Telegram Botu ve Yedek Dosyası** | Devir bildirimleri ve tek tıkla tam `.json` sistem yedeğini doğrudan Telegram botunuza belge olarak iletme imkanı. **SOCKS5** desteği. |
| 💎 **Modern Cam Efektli (Glassmorphic) UI** | Koyu ve açık tema seçenekleri, 6 dil desteği (İngilizce, Farsça, Rusça, Çince, Türkçe, Arapça) ve kusursuz mobil uyumluluk. |
| 📜 **Şeffaf Denetim Kayıtları** | Olay türüne göre renklendirilmiş kayıtlar, yenileme ve kalıcı temizleme seçenekleri. |

---

## ⚡ Tek Komutla Kolay Kurulum (Ubuntu / Debian)

Sunucunuzda `root` yetkisiyle çalıştırın:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/a-salemi/Virtualizor-Traffic-Rollover/main/install.sh)"
```

---

## 🔄 Hızlı Güncelleme

Mevcut kurulumunuzu hiçbir veri kaybetmeden güncellemek için:

```bash
cd /opt/virturoll && git pull && ./venv/bin/pip install -r backend/requirements.txt && systemctl restart virturoll
```

---

## ⚙️ Virtualizor Panel Bağlantı Rehberi

1. **Virtualizor Admin Panelinizde** **Configuration** -> **API Credentials** bölümüne gidin ve API anahtarı oluşturun.
2. **Önemli:** **Allowed IPs** kısmına VirtuRoll sunucunuzun IP adresini yazın.
3. VirtuRoll paneline girip **Paneller** -> **+ Panel Ekle** butonuna tıklayın.
4. IP/Domain, Port (`4085`), API Key ve API Password girerek kaydedin.

---

## 🤖 Telegram Bildirimleri ve Yedekleme

1. [@BotFather](https://t.me/BotFather) üzerinden bir bot oluşturup token alın.
2. [@userinfobot](https://t.me/userinfobot) ile Chat ID numaranızı öğrenin.
3. VirtuRoll'da **Ayarlar** -> **Telegram Bot Bildirimleri** alanına girip kaydedin.
4. **Yedekleme ve Geri Yükleme** bölümündeki **Yedeği Telegram'a Gönder** butonu ile veritabanınızı güvenle Telegram'a ulaştırın.

---

## 🛠️ Servis Yönetimi

```bash
sudo systemctl status virturoll   # Durumu kontrol et
sudo journalctl -u virturoll -f   # Canlı günlükleri incele
sudo systemctl restart virturoll  # Servisi yeniden başlat
sudo systemctl stop virturoll     # Servisi durdur
```

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak yayımlanmıştır.  
Geliştirici: Amir Salemi (2026).
