# الخطوة الأولى: استخدام نسخة نود كاملة ومستقرة بدل alpine عشان أدوات البناء تكون متوفرة
FROM node:18-slim AS node_builder
WORKDIR /app

# تثبيت أدوات البناء الأساسية المطلوبة لمكتبات الواتساب الكبيرة
RUN apt-get update && apt-get install -y python3 make g++ git && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN npm install
COPY index.js ./

# الخطوة الثانية: بناء البيئة النهائية المدمجة (بايثون + نود)
FROM python:3.10-slim
WORKDIR /app

# تثبيت Node.js جوة حاوية البايثون
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# نسخ مكتبات وملفات الواتساب من الخطوة الأولى
COPY --from=node_builder /app /app

# نسخ ملفات البايثون وتثبيت مكتباتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot.py .

# فتح المنفذ 3000 اللي حيتكلموا بيه داخلياً
EXPOSE 3000

# الأمر النهائي لتشغيل البوت (وهو تلقائياً حيشغل النود معاه)
CMD ["python", "bot.py"]
