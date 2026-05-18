# استخدام نسخة نود الرسمية والمستقرة كأساس
FROM node:18-slim

# تحديد مجلد العمل
WORKDIR /app

# تثبيت البايثون والأدوات الأساسية بأمر واحد سريع وخفيف
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# نسخ ملفات تعريف المكتبات للـ Node والبايثون
COPY package*.json ./
COPY requirements.txt .

# تثبيت مكتبات البايثون
RUN pip3 install --no-cache-dir -r requirements.txt

# تثبيت مكتبات النود (مع تجاهل النصوص البرمجية الثقيلة وقت البناء لتوفير الذاكرة)
RUN npm install --production --ignore-scripts

# نسخ باقي ملفات المشروع للواجهة
COPY index.js .
COPY bot.py .

# فتح المنفذ 3000 المشترك داخلياً
EXPOSE 3000

# تشغيل البوت تلقائياً
CMD ["python3", "bot.py"]
