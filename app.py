from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.integrate import simpson
from scipy.interpolate import make_interp_spline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def rasional(x, a, b, c):
    return (a * x + b) / (x + c)

def harga_model(x, a, b, c):
    return a + b * np.sin(c * x)

def jual_model(x, a, b, c):
    return a + b * np.cos(c * x)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/feature1", methods=["GET", "POST"])
def feature1():
    error = None
    df = None
    default_data = {
        'jumlah_pesanan': [10, 15, 20, 25, 30, 35, 40],
        'penggunaan_bahan_baku': [5.1, 6.8, 9.1, 10.2, 12.3, 13.5, 15.0]
    }
    data_rows = []
    x_test = 30

    try:
        if request.method == "POST":
            jumlah_pesanan_list = request.form.getlist("jumlah_pesanan[]")
            bahan_baku_list = request.form.getlist("bahan_baku[]")
            x_test_input = request.form.get("x_test")

            if x_test_input:
                x_test = int(x_test_input)

            if jumlah_pesanan_list and bahan_baku_list:
                data = []
                for jp, bb in zip(jumlah_pesanan_list, bahan_baku_list):
                    if jp.strip() and bb.strip():
                        data.append({
                            "jumlah_pesanan": float(jp),
                            "penggunaan_bahan_baku": float(bb)
                        })
                if data:
                    df = pd.DataFrame(data)
                    data_rows = data
        else:
            df = pd.DataFrame(default_data)
            data_rows = df.to_dict("records")

        if df is None or df.empty:
            raise ValueError("Data input tidak boleh kosong.")

        df = df.sort_values("jumlah_pesanan")
        if df["jumlah_pesanan"].duplicated().any():
            raise ValueError("Jumlah pesanan tidak boleh mengandung duplikat.")

        x_data = df['jumlah_pesanan'].to_numpy()
        y_data = df['penggunaan_bahan_baku'].to_numpy()

        popt, _ = curve_fit(rasional, x_data, y_data)
        a, b, c = popt

        x_pred = np.linspace(min(x_data), max(x_data), 100)
        y_pred = rasional(x_pred, *popt)

        spline = make_interp_spline(x_data, y_data, k=3)
        x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
        y_smooth = spline(x_smooth)

        fig, ax = plt.subplots()
        ax.scatter(x_data, y_data, label='Data Asli', color='blue')
        ax.plot(x_smooth, y_smooth, color='green', label='Interpolasi Data (Spline)')
        ax.plot(x_pred, y_pred, label=f'Q(x) = ({a:.2f}x + {b:.2f}) / (x + {c:.2f})', color='red')
        ax.set_xlabel("Jumlah Pesanan Harian")
        ax.set_ylabel("Penggunaan Bahan Baku (kg)")
        ax.set_title("Pemodelan Hubungan Pesanan dan Bahan Baku")
        ax.legend()
        ax.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        grafik_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        prediksi_harian = [(x, rasional(x, *popt)) for x in [10, 20, 30, 40, 50, 60]]
        total_mingguan = sum([rasional(x, *popt) for x in df["jumlah_pesanan"]])
        q_test = rasional(x_test, *popt)

        return render_template("feature1.html",
            grafik=grafik_base64,
            a=a, b=b, c=c,
            x_test=x_test, q_test=q_test,
            prediksi_harian=prediksi_harian,
            total_mingguan=total_mingguan,
            error=error,
            data=data_rows
        )

    except Exception as e:
        error = str(e)
        return render_template("feature1.html",
            grafik=None,
            a=0, b=0, c=0,
            x_test=x_test, q_test=0,
            prediksi_harian=[],
            total_mingguan=0,
            error=error,
            data=data_rows if data_rows else default_data
        )

@app.route("/feature2", methods=["GET", "POST"])
def feature2():
    error = None
    grafik_base64 = ""
    default_data = {
        'biaya_total': [10000, 17000, 74500, 58000, 19000],
        'jumlah_terjual': [10, 12, 80, 44, 29]
    }
    data_rows = []
    biaya_tetap = 5000
    harga_manual = 0
    harga_rata_rata = 0
    model_formula = ""
    prediksi_harian = []

    try:
        if request.method == "POST":
            jumlah_list = request.form.getlist("jumlah_terjual[]")
            biaya_list = request.form.getlist("biaya_total[]")
            biaya_tetap_input = request.form.get("biaya_tetap")
            if biaya_tetap_input:
                biaya_tetap = float(biaya_tetap_input)

            data = []
            for jt, bt in zip(jumlah_list, biaya_list):
                if jt.strip() and bt.strip():
                    data.append({
                        "jumlah_terjual": float(jt),
                        "biaya_total": float(bt)
                    })
            if data:
                df = pd.DataFrame(data)
                data_rows = data
        else:
            df = pd.DataFrame(default_data)
            data_rows = df.to_dict("records")

        if df.empty:
            raise ValueError("Data input tidak boleh kosong.")

        df = df.sort_index()
        x_data = np.arange(1, len(df) + 1)

        # 🔸 Hitung biaya per unit
        df["biaya_per_unit"] = df["biaya_total"] / df["jumlah_terjual"]
        biaya_per_unit = df["biaya_per_unit"].to_numpy()

        # 🔸 Buat fungsi polinomial interpolasi biaya per unit
        poly = np.poly1d(np.polyfit(x_data, biaya_per_unit, 2))

        # 🔸 Definisikan fungsi integral biaya per unit + biaya tetap
        def integran(x):
            return poly(x) + biaya_tetap

        # 🔸 Buat y_data hasil integral di titik diskrit
        y_data = integran(x_data)

        # 🔸 Fitting ke model rasional
        def rasional(x, a, b, c):
            return (a * x + b) / (x + c)

        popt, _ = curve_fit(rasional, x_data, y_data)
        a, b, c = popt

        # 🔸 Plot grafik
        x_pred = np.linspace(1, len(x_data), 100)
        y_pred = integran(x_pred)
        y_fit = rasional(x_pred, *popt)

        fig, ax = plt.subplots()
        ax.plot(x_pred, y_pred, label="Hasil Integral (Interpolasi)", color='green')
        ax.scatter(x_data, y_data, label="Nilai Integral (Diskrit)", color='blue')
        ax.plot(x_pred, y_fit, label=f'Fitting: ({a:.2f}x + {b:.2f}) / (x + {c:.2f})', color='red')
        ax.set_xlabel("Hari ke-x")
        ax.set_ylabel("Harga Jual per Unit (Rp)")
        ax.set_title("Prediksi Harga Jual Optimal")
        ax.legend()
        ax.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        grafik_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # 🔸 Perhitungan hasil
        harga_manual = integran(3)
        harga_rata_rata = np.mean(y_data)
        prediksi_harian = [(int(x), integran(x)) for x in x_data]
        model_formula = f"({a:.2f}x + {b:.2f}) / (x + {c:.2f})"

        return render_template("feature2.html",
            grafik=grafik_base64,
            model_formula=model_formula,
            harga_manual=harga_manual,
            harga_rata_rata=harga_rata_rata,
            prediksi_harian=prediksi_harian,
            data=data_rows,
            biaya_tetap=biaya_tetap,
            error=None
        )

    except Exception as e:
        error = str(e)
        return render_template("feature2.html",
            grafik=None,
            model_formula="-",
            harga_manual=None,
            harga_rata_rata=None,
            prediksi_harian=[],
            data=data_rows if data_rows else default_data,
            biaya_tetap=biaya_tetap,
            error=error
        )
    
@app.route("/feature3", methods=["GET", "POST"])
def feature3():
    error = None
    grafik_base64 = ""
    model_formula = ""
    total_pendapatan = 0
    pendapatan_harian = []
    
    default_data = {
        'harga_jual': [15000, 16000, 15500, 16500, 15800],
        'jumlah_terjual': [100, 110, 105, 115, 108]
    }
    data_rows = []

    try:
        if request.method == "POST":
            harga_list = request.form.getlist("harga_jual[]")
            jumlah_list = request.form.getlist("jumlah_terjual[]")
            data = []
            for h, j in zip(harga_list, jumlah_list):
                if h.strip() and j.strip():
                    data.append({
                        "harga_jual": float(h),
                        "jumlah_terjual": float(j)
                    })
            if not data:
                raise ValueError("Data tidak boleh kosong.")
            df = pd.DataFrame(data)
            data_rows = data
        else:
            df = pd.DataFrame(default_data)
            data_rows = df.to_dict("records")

        df = df.sort_index()
        x_data = np.arange(1, len(df) + 1)
        P_data = df["harga_jual"].to_numpy()
        S_data = df["jumlah_terjual"].to_numpy()

        popt_P, _ = curve_fit(harga_model, x_data, P_data)
        popt_S, _ = curve_fit(jual_model, x_data, S_data)

        x_pred = np.linspace(1, len(x_data), 100)
        P_fit = harga_model(x_pred, *popt_P)
        S_fit = jual_model(x_pred, *popt_S)
        Pendapatan_fit = P_fit * S_fit
        Pendapatan_asli = P_data * S_data

        total_pendapatan = simpson(Pendapatan_fit, x=x_pred)

        fig, ax = plt.subplots()
        ax.scatter(x_data, Pendapatan_asli, label="Data Asli", color="red")
        ax.plot(x_data, P_data * S_data, color="green", label="Garis Data Asli")
        ax.plot(x_pred, Pendapatan_fit, color="blue", label="Kurva Fitting Pendapatan")
        ax.set_xlabel("Hari ke-")
        ax.set_ylabel("Pendapatan (Rp)")
        ax.set_title("Optimasi Pendapatan Harian")
        ax.legend()
        ax.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        grafik_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        model_formula = {
            "P": f"{popt_P[0]:.2f} + {popt_P[1]:.2f} * sin({popt_P[2]:.2f} * x)",
            "S": f"{popt_S[0]:.2f} + {popt_S[1]:.2f} * cos({popt_S[2]:.2f} * x)"
        }

        for x in [5, 10, 15, 20, 25, 30]:
            p = harga_model(x, *popt_P)
            s = jual_model(x, *popt_S)
            pendapatan_harian.append((x, p * s))

        return render_template("feature3.html",
            grafik=grafik_base64,
            model_formula=model_formula,
            total_pendapatan=total_pendapatan,
            pendapatan_harian=pendapatan_harian,
            data=data_rows,
            error=error
        )
    
    except Exception as e:
        error = str(e)
        return render_template("feature3.html",
            grafik=None,
            model_formula="",
            total_pendapatan=0,
            pendapatan_harian=[],
            data=data_rows if data_rows else default_data,
            error=error
        )
    
@app.route("/feature4", methods=["GET", "POST"])
def feature4():
    error = None
    grafik_base64 = ""
    model_formula = ""
    total_biaya = 0
    biaya_harian = []

    default_data = {
        'jumlah_pesanan': [50, 60, 55, 65, 58],
        'biaya_produksi': [500, 600, 530, 670, 590]
    }
    data_rows = []

    try:
        if request.method == "POST":
            pesanan_list = request.form.getlist("jumlah_pesanan[]")
            biaya_list = request.form.getlist("biaya_produksi[]")
            data = []
            for p, b in zip(pesanan_list, biaya_list):
                if p.strip() and b.strip():
                    data.append({
                        "jumlah_pesanan": float(p),
                        "biaya_produksi": float(b)
                    })
            if not data:
                raise ValueError("Data tidak boleh kosong.")
            df = pd.DataFrame(data)
            data_rows = data
        else:
            df = pd.DataFrame(default_data)
            data_rows = df.to_dict("records")

        df = df.sort_values(by="jumlah_pesanan")
        x_data = df["jumlah_pesanan"].to_numpy()
        y_data = df["biaya_produksi"].to_numpy()

        coef = np.polyfit(x_data, y_data, deg=2)
        model = np.poly1d(coef)

        x_pred = np.linspace(min(x_data), max(x_data), 100)
        y_pred = model(x_pred)
        y_data_pred = model(x_data)

        total_biaya = simpson(y_pred, x_pred)

        fig, ax = plt.subplots()
        ax.scatter(x_data, y_data, color="red", label="Data Asli")
        x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
        spline = make_interp_spline(x_data, y_data, k=2)  # spline derajat 2 biar smooth tapi tetap stabil
        y_smooth = spline(x_smooth)
        ax.plot(x_smooth, y_smooth, color="green", label="Garis Data Asli")
        ax.plot(x_pred, y_pred, color="blue", label="Kurva Fitting")
        ax.set_xlabel("Jumlah Pesanan")
        ax.set_ylabel("Biaya Produksi (ribu rupiah)")
        ax.set_title("Analisis Biaya Produksi")
        ax.legend()
        ax.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        grafik_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        model_formula = f"{coef[0]:.2f}x² + {coef[1]:.2f}x + {coef[2]:.2f}"

        for x in [50, 100, 150, 200, 250, 300]:
            biaya = model(x)
            biaya_harian.append((x, biaya))

        return render_template("feature4.html",
            grafik=grafik_base64,
            model_formula=model_formula,
            total_biaya=total_biaya,
            biaya_harian=biaya_harian,
            data=data_rows,
            error=error
        )
    
    except Exception as e:
        error = str(e)
        return render_template("feature4.html",
            grafik=None,
            model_formula="",
            total_biaya=0,
            biaya_harian=[],
            data=data_rows if data_rows else default_data,
            error=error
        )


if __name__ == "__main__":
    app.run(debug=True)
