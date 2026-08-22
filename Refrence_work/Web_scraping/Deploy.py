from flask import Flask, request, render_template_string
import joblib
import numpy as np

app = Flask(__name__)

# حمّل الموديل (تأكد إن ملف kia_model.pkl في نفس مجلد السكربت)
model = joblib.load('kia_model.pkl')

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مُنبئ أسعار سيارات كيا</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }

        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }

        button {
            width: 100%;
            padding: 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
        }

        button:hover {
            background: #0056b3;
        }

        .result {
            margin-top: 30px;
            padding: 20px;
            background: #e8f5e8;
            border-radius: 5px;
            text-align: center;
            display: none;
        }

        .price {
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
        }

        .loading {
            display: none;
            text-align: center;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 مُنبئ أسعار سيارات كيا المستعملة</h1>
        
        <form id="carForm">
            <div class="form-group">
                <label for="year">سنة الصنع:</label>
                <select id="year" required>
                    <option value="">اختر سنة الصنع</option>
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                    <option value="2022">2022</option>
                    <option value="2021">2021</option>
                    <option value="2020">2020</option>
                    <option value="2019">2019</option>
                    <option value="2018">2018</option>
                    <option value="2017">2017</option>
                    <option value="2016">2016</option>
                    <option value="2015">2015</option>
                    <option value="2014">2014</option>
                    <option value="2013">2013</option>
                    <option value="2012">2012</option>
                    <option value="2011">2011</option>
                    <option value="2010">2010</option>
                </select>
            </div>

            <div class="form-group">
                <label for="km">المسافة المقطوعة (كيلومتر):</label>
                <input type="number" id="km" placeholder="مثال: 50000" min="0" required>
            </div>

            <button type="submit">احسب السعر المتوقع</button>
        </form>

        <div class="loading" id="loading">
            جاري حساب السعر...
        </div>

        <div class="result" id="result">
            <div class="price" id="price"></div>
            <p>السعر التقديري للسيارة</p>
            <small>* هذا تقدير تقريبي وقد يختلف السعر الفعلي</small>
        </div>
    </div>

    <script>
        // بيانات مبسطة للسيارات
        const carData = [
            {year: 2014, km: 43000, price: 850000},
            {year: 2025, km: 9000, price: 1499000},
            {year: 2011, km: 192000, price: 560000},
            {year: 2022, km: 100000, price: 1120000},
            {year: 2018, km: 85000, price: 775000},
            {year: 2020, km: 45000, price: 950000},
            {year: 2016, km: 120000, price: 620000},
            {year: 2019, km: 60000, price: 890000},
            {year: 2021, km: 30000, price: 1180000},
            {year: 2015, km: 150000, price: 540000}
        ];

        // دالة التنبؤ بالسعر
        function predictPrice(year, km) {
            const currentYear = 2025;
            const carAge = currentYear - year;
            
            // سعر أساسي حسب العمر
            let basePrice = 2000000 - (carAge * 70000);
            
            // خصم حسب المسافة
            const kmPenalty = km * 2.5;
            basePrice -= kmPenalty;
            
            // البحث عن سيارات مشابهة
            const similarCars = carData.filter(car => 
                Math.abs(car.year - year) <= 2
            );
            
            if (similarCars.length > 0) {
                const avgPrice = similarCars.reduce((sum, car) => sum + car.price, 0) / similarCars.length;
                basePrice = (basePrice + avgPrice) / 2;
            }
            
            // حد أدنى للسعر
            basePrice = Math.max(basePrice, 300000);
            
            return Math.round(basePrice);
        }

        // تنسيق السعر
        function formatPrice(price) {
            return price.toLocaleString('ar-EG') + ' جنيه مصري';
        }

        // معالج النموذج
        document.getElementById('carForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const year = parseInt(document.getElementById('year').value);
            const km = parseInt(document.getElementById('km').value);
            
            // إخفاء النتيجة وإظهار التحميل
            document.getElementById('result').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            
            // محاكاة وقت المعالجة
            setTimeout(() => {
                const predictedPrice = predictPrice(year, km);
                
                // إظهار النتيجة
                document.getElementById('price').textContent = formatPrice(predictedPrice);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('result').style.display = 'block';
            }, 1000);
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def predict():
    prediction = None
    if request.method == "POST":
        try:
            car_model = int(request.form["car_model"])
            km_traveled = float(request.form["km_traveled"])
            features = np.array([[car_model, km_traveled]])
            result = model.predict(features)[0]
            prediction = round(result, 2)
        except Exception as e:
            prediction = f"Error: {e}"
    return render_template_string(HTML, prediction=prediction)

if __name__ == "__main__":
    # اجعل السيرفر يستمع على كل العناوين عشان تقدر توصله من أي جهاز بالشبكة
    app.run(host='0.0.0.0', port=5000, debug=True)

