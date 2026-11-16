# Hiv-Drc-Model — 安裝與使用

[English](USAGE.md) · **繁體中文** · [← 回到 README](../README.zh-TW.md)

如何安裝套件、使用命令列、Python API 與互動式儀表板，以及各檔案的位置。分析結果本身在 [REPORT.zh-TW.md](REPORT.zh-TW.md)。

## 目錄

- [安裝](#安裝)
- [使用方式](#使用方式)
- [輸出圖表](#輸出圖表)
- [專案結構](#專案結構)

---

## 安裝

需要 Python 3.10 或更新版本。

```bash
git clone https://github.com/heinricitorgau/hiv-drc-model.git
cd hiv-drc-model
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

或者不安裝套件，只裝相依套件（這個檔案是 pyproject 的鏡像，留給從 requirements 檔安裝的部署環境）：

```bash
pip install -r requirements.txt
```

開發用（加上 pytest 和 ruff）：

```bash
pip install -e ".[dev]"
```

[互動式儀表板](#互動式儀表板)用（加上 streamlit）：

```bash
pip install -e ".[app]"
```

相依套件只有 `numpy`、`scipy`、`matplotlib` 和 `emcee`。Streamlit 只有 `app.py` 需要，放在 `app` extra 裡，所以 import `hiv_drc` 永遠不會順帶載入網頁框架。

---

## 使用方式

### 命令列

執行全部流程，並把十二張圖寫進 `figures/`：

```bash
python -m hiv_drc
```

六個階段分別是 `dynamics`、`r0`、`stability`、`sensitivity`、`estimate` 和 `bayes`，可以用名稱只選其中幾個：

```bash
python -m hiv_drc dynamics
```

```bash
python -m hiv_drc r0 stability
```

產生含噪資料，再從資料中找回參數：

```bash
python -m hiv_drc estimate --noise 0.05 --starts 8 --data data/synthetic/observations.csv
```

不求點估計，改為對後驗分布取樣：

```bash
python -m hiv_drc bayes --noise 0.05 --mcmc-walkers 16 --mcmc-steps 1000
```

常用選項：

| 旗標 | 預設值 | 作用 |
| --- | --- | --- |
| `--outdir DIR` | `figures` | PNG 的輸出位置 |
| `--years N` | `50` | 動態模擬的時間長度 |
| `--samples N` | `1000` | 拉丁超立方取樣的樣本數 |
| `--spread F` | `0.25` | 取樣範圍的相對半寬 |
| `--sweep-points N` | `41` | 分岔掃描的點數 |
| `--show` | 關閉 | 以互動方式開啟圖表，而不只是存檔 |
| `--no-save` | 關閉 | 不寫出 PNG |

`estimate` 階段的選項：

| 旗標 | 預設值 | 作用 |
| --- | --- | --- |
| `--fit PARAM...` | `beta alpha` | 要找回哪些參數 |
| `--noise F` | `0.05` | 合成資料的相對量測噪音 |
| `--noise-model M` | `proportional` | `proportional`（比例）或 `constant`（固定）量測誤差 |
| `--obs-years N` | `30` | 觀測期間的長度 |
| `--obs-points N` | `31` | 觀測點數 |
| `--seed N` | `20260830` | 噪音與多起點抽樣的亂數種子 |
| `--starts N` | `8` | 最佳化器的多起點重啟次數 |
| `--weights W` | `scale` | 殘差加權方式：`scale`、`sigma` 或 `none` |
| `--grid N` | `41` | 目標函數曲面網格的解析度 |
| `--data PATH` | 無 | 把合成觀測寫進這個 CSV |

`bayes` 階段的選項（另外也使用上面與 `estimate` 共用的 `--fit`、`--noise`、`--noise-model`、`--obs-years`、`--obs-points` 和 `--seed`）：

| 旗標 | 預設值 | 作用 |
| --- | --- | --- |
| `--mcmc-walkers N` | `16` | MCMC 取樣器的系集大小 |
| `--mcmc-steps N` | `1000` | 每個 walker 的步數 |
| `--mcmc-burn N` | `250` | 當作 burn-in 捨棄的步數 |

用預設值大約會跑 16,000 次正向模型；依機器不同，需要幾十秒到幾分鐘。

執行 `pip install -e .` 之後，同樣的功能也可以用 console script 呼叫：

```bash
hiv-drc --samples 2000 --outdir results
```

### 當作函式庫使用

```python
from hiv_drc import DRC_2020, reproduction_number, simulate

result = reproduction_number(DRC_2020)
print(result)                      # R0 = 1.214450 (R1 = 48.543689, ...)

solution = simulate(DRC_2020, t_span=(0.0, 50.0))
print(solution["I1"][-1])          # t = 50 時不知情的感染者
print(solution.prevalence[-1])     # 感染者占總人口的比例
```

參數是不可變的 dataclass，所以情境是用複製而不是修改來建立：

```python
from hiv_drc import critical_beta, endemic_equilibrium

intervention = DRC_2020.replace(phi=0.09, alpha=0.05, sigma1=0.0125)
print(reproduction_number(intervention).R0)     # 0.7644，低於閾值

print(critical_beta(DRC_2020))                  # 0.123513

equilibrium = endemic_equilibrium(DRC_2020)
print(equilibrium.infected, equilibrium.is_stable)
```

從資料找回參數只要三行：

```python
from hiv_drc import generate_observations, estimate_parameters

observations = generate_observations(noise=0.05, seed=20260830)   # 或 Observations.from_csv
fit = estimate_parameters(observations, fit=("beta", "alpha"))
print(fit.summary())
```

```
  param        estimate     std err                     95% CI      truth      error   rel err
  beta         0.165803    0.074724   [  0.016333,   0.315274]   0.150000  +0.015803   +10.54%
  alpha        0.037321    0.005075   [  0.027170,   0.047473]   0.035000  +0.002321    +6.63%

  cost = 1.648974e-01   RMSE (millions)   A: 0.004153   T: 0.005151
  R0 at the estimate = 1.342384
  corr(beta, alpha) = +0.1184
```

改成對後驗取樣只要再多一行，而它回答的是另一個問題：不是「最佳擬合是什麼」，而是「資料實際排除了哪些可能」：

```python
from hiv_drc import run_mcmc

posterior = run_mcmc(observations, fit=("beta", "alpha"), n_walkers=16, n_steps=600, burn=150)
print(posterior.summary())
```

```
  param            median         std                     95% CI   R-hat      ESS
  beta           0.145171    0.021042   [  0.095625,   0.175486]   1.162      n/a   truth 0.150000  (-3.22%)
  alpha          0.034575    0.002350   [  0.030047,   0.039226]   1.146      n/a   truth 0.035000  (-1.22%)
  eta_A          0.046998    0.006543   [  0.037134,   0.062503]   1.109      n/a
  eta_T          0.056340    0.007368   [  0.044648,   0.074339]   1.157      n/a

  acceptance fraction 0.587   16 walkers x 600 steps (150 discarded as burn-in)
  R0 at the posterior median = 1.175355
```

`eta_A` 和 `eta_T` 不是流行病學參數，而是每個序列自己推論出的相對量測噪音水準，是一起擬合出來的，不是假設的。

### 互動式儀表板

`app.py` 把模型放進瀏覽器介面，不用寫程式就能探索各種情境。線上部署版在 [hiv-drc-model-6h4eabztaookr4gj4steeg.streamlit.app](https://hiv-drc-model-6h4eabztaookr4gj4steeg.streamlit.app)；要在本機執行：

```bash
pip install -e ".[app]"
streamlit run app.py
```

共有三個分頁。**Dynamics** 用滑桿調整 $\beta$、$\alpha$ 和 $\phi$，每次變動都用封閉形式重算 $R_0$，並顯示它的 $R_1/R_2/R_3$ 分解，以及 $I_1$、$I_2$、$A$、$T$ 的軌跡。**The inverse problem** 用目前的參數產生含噪的 $A$ 和 $T$，用 `estimate_parameters` 找回參數，並把 Wald 區間和估計器從沒看過的真值放在一起比較。**Real data and the scale-up** 完全不用合成資料：它用 `load_worldbank` 載入 UNAIDS 序列，用第一年的 PLHIV、ART 覆蓋率和人口建立初始狀態（而不是用表 2），再把發布的 `plhiv` 和 `art_coverage` 畫在模型旁邊。

第三個分頁就是設計來切換的。在常數速率下，模型到 2024 年只達到 34% 的 ART 覆蓋率，而發布值是 71%，因為常數的 $\alpha$ 畫不出 S 形曲線。打開 logistic 擴大、滑桿維持預設值，覆蓋率落在 70.9%，但 PLHIV 是 0.173 百萬，而發布值是 0.540。一個序列準到零點一個百分點、另一個卻差了三倍，這正是[面對真實資料](REPORT.zh-TW.md#面對真實資料)整節的重點，只要勾一個核取方塊就看得到。

儀表板本身不計算任何東西：螢幕上每個數字都來自 `DRC_2020`、`simulate`、`reproduction_number`、`generate_observations` 和 `estimate_parameters`。它只是一個檢視，不是第二套實作，所以不會和有測試的那一套漸漸不一致。

有安裝 CJK 字型時，圖表用中文標示，沒有時用英文。matplotlib 遇到缺字不會報錯，而是畫出空白方框，所以在精簡的 Linux 容器上，每個標籤都會靜悄悄地變成方框。

$S$ 和 $R$ 預設隱藏，而不是畫在第二個縱軸上：$S$ 約 88 百萬，$A$ 約 0.05 百萬，同一張圖上兩種縱軸刻度會讓斜率無法比較。勾選核取方塊會把它們加成共用時間軸的第二個面板。

參數選單值得試試預設以外的選項。在滑桿的基準值和 5% 噪音下，擬合 $\beta$ 和 $\alpha$ 能找回到 +10.5% 和 +6.6%，cost 為 0.1649。在同一次擬合中加入 $\phi$，cost 變成 0.1642，幾乎沒變，但 $\beta$ 變成 $1.00 \pm 21.5$，$\phi$ 撞到上界變成 $1.00 \pm 23.7$，兩個區間都跨過零。殘差幾乎沒察覺，參數卻已經失去意義。這就是擴大期研究遇到的[同一種不可識別性](REPORT.zh-TW.md#但九參數模型無法識別)，從下拉選單就能看到；這也是為什麼估計值旁邊總是附上相關係數和標準誤，而不是只給點估計。

---

## 輸出圖表

十二張圖都寫進 `figures/`（被 git 忽略，一個指令就能重新產生）。

| 檔案 | 內容 |
| --- | --- |
| `01_population_dynamics.png` | 四個面板：未感染倉室（$S$、$R$）、感染倉室（$I_1$、$I_2$、$A$、$T$）、總人口對照承載量，以及盛行率。$S$ 和 $R$ 與感染類別分開畫，因為兩者差了三個數量級。 |
| `02_scenarios.png` | 基準情境、提高接觸率（$\beta = 0.2$）以及論文的加強介入情境下的總感染人口，各自標上 $R_0$。 |
| `03_r0_surface.png` | $(\beta, \sigma_1)$ 平面上的 $R_0$。左：填色等高線，標出 $R_0 = 1$ 閾值和 DRC 的現況點。右：同一個曲面的 3D 圖，用半透明的 $R_0 = 1$ 平面切開，交線以黑色畫出。 |
| `04_bifurcation.png` | 地方性感染水準對 $R_0$，以及無病平衡點與吸引子上的主導 Jacobian 特徵值。這是前向跨臨界分岔的圖像。 |
| `05_local_sensitivity.png` | 論文正規化敏感度指標的龍捲風圖。 |
| `06_global_sensitivity.png` | 拉丁超立方／PRCC 篩選：$R_0$ 的 PRCC、全域與局部的比較、50 年感染總數的 PRCC，以及取樣得到的 $R_0$ 分布。 |
| `07_parameter_fit.png` | 反問題：$A$ 和 $T$ 的含噪觀測畫成散點、找回的模型畫成曲線、產生資料的軌跡以虛線畫在底下、殘差，以及每個估計值對照真值與 95% 區間。 |
| `08_cost_surface.png` | $(\beta, \alpha)$ 平面上的目標函數，以對數色階呈現，標出真實參數、最小平方估計和 95% 信賴框。盆地的形狀就是可識別性的診斷。 |
| `09_posterior.png` | $\beta$、$\alpha$ 和兩個擬合噪音水準的兩兩邊際後驗，也就是 MCMC 的「corner plot」。圓形的點雲代表這一對參數可以分別識別；拉長的點雲代表只有它們的某種組合可以識別。 |
| `10_trace.png` | 每個參數的 walker 軌跡：每個 walker 在保留步數內的路徑，並標上它的 split-$\hat R$。模糊的水平帶是混合良好的鏈；明顯分開的 walker 則不是。 |
| `11_posterior_predictive.png` | 觀測到的 $A$ 和 $T$ 對照後驗*預測*帶（模型加上每次抽樣自己擬合的噪音），每個面板都報告實際落在帶內的點所占比例。 |
| `12_bayes_vs_frequentist.png` | 同一次擬合的最小平方 Wald 區間和 MCMC 可信區間，畫在同一個軸上。兩者不一致的地方，代表 Wald 區間背後的二次近似已經開始失效。 |

---

## 專案結構

```
hiv-drc-model/
├── src/hiv_drc/
│   ├── __init__.py          公開 API
│   ├── __main__.py          讓 `python -m hiv_drc` 可以執行
│   ├── parameters.py        表 2 和表 3，也就是設定區塊
│   ├── model.py             ODE 右側函數與它的 Jacobian
│   ├── simulation.py        solve_ivp 包裝與 Solution 型別
│   ├── reproduction.py      R0：封閉形式與次世代矩陣
│   ├── equilibria.py        無病與地方性平衡點、穩定性
│   ├── sensitivity.py       局部指標、拉丁超立方取樣、PRCC
│   ├── analysis.py          參數掃描：R0 網格、分岔、閾值
│   ├── observables.py       監測系統報告的數量，寫成狀態的函數
│   ├── priors.py            資訊性先驗與收縮診斷
│   ├── realdata.py          載入 UNAIDS／世界銀行序列；從資料建立初始狀態
│   ├── synthetic.py         模擬資料：正向模型 + 高斯量測誤差
│   ├── estimation.py        反問題：有界非線性最小平方法
│   ├── bayesian.py          同一個反問題，用 MCMC（emcee）求解
│   ├── plotting.py          圖表（這裡不做任何計算）
│   └── cli.py               命令列介面
├── tests/                   222 個測試（含 doctest 共 238 個）
│   ├── conftest.py          共用 fixture
│   ├── test_model.py        ODE 右側函數與 Jacobian
│   ├── test_simulation.py   積分、守恆、求解器一致性
│   ├── test_reproduction.py 封閉形式 R0 對照次世代矩陣
│   ├── test_equilibria.py   平衡點與穩定性定理
│   ├── test_sensitivity.py  局部指標與 PRCC
│   ├── test_observables.py  算子，以它們之間的恆等式檢查
│   ├── test_realdata.py     單位、缺值，以及表 2 的不一致
│   ├── test_scaleup.py      隨時間變化的速率，以及結構性上限
│   ├── test_priors.py       密度，以及已知答案案例上的收縮量
│   ├── test_synthetic.py    資料產生器
│   ├── test_estimation.py   找回、邊界、不確定性、可識別性
│   ├── test_bayesian.py     先驗、概似、split-R-hat、MCMC 找回
│   └── test_app.py          儀表板，透過 Streamlit 的 AppTest 驅動
├── notebooks/
│   ├── 01_inverse_problem.ipynb       估計流程的解說導覽
│   └── 02_bayesian_uncertainty.ipynb  同一個擬合改用 MCMC，以及兩者在哪裡不一致
├── scripts/
│   ├── coverage_study.py    貝氏覆蓋率表背後的一次性量測
│   ├── observability_study.py  哪些觀測組合能識別速率
│   ├── fetch_worldbank.py   下載 DRC 指標（唯一的網路存取）
│   ├── realdata_fit.py      逐個期間擬合真實序列
│   ├── scaleup_fit.py       常數 vs alpha(t) vs alpha(t)+lambda(t)
│   ├── prior_contraction.py  資訊性先驗的區間是否名副其實
│   └── readme_figures.py    重新產生 README 內嵌的圖（docs/img/）
├── data/
│   ├── README.md            資料來源與欄位定義
│   ├── real/                DRC 的 UNAIDS／世界銀行快照
│   └── synthetic/           產生的觀測資料（`--data` 寫在這裡）
├── docs/
│   ├── REPORT.md            完整的結果分析報告
│   ├── USAGE.md             安裝、命令列、API、儀表板（本檔為中文版）
│   ├── *.zh-TW.md           繁體中文版
│   └── img/                 README 顯示的圖（有 commit）
├── figures/                 產生的輸出（被 git 忽略）
├── assets/                  README 橫幅
├── app.py                   Streamlit 儀表板，只負責呈現，不做計算
├── pyproject.toml
├── requirements.txt        pyproject 執行期相依套件的部署鏡像
├── CITATION.cff             引用資訊（GitHub 的「Cite this repository」）
├── README.md                概覽與主要結果（英文）
└── README.zh-TW.md          繁體中文版
```

分層是刻意的：`plotting.py` 從不計算，分析模組從不繪圖，所以重新調整一張圖的樣式不必重跑兩萬年的積分，而且每個分析模組在沒有顯示器的機器上也都能 import。

估計層也有同樣的分離。`synthetic.py` 知道資料怎麼產生，對擬合一無所知；`estimation.py` 知道怎麼擬合，只有在*評分*結果時才會用到產生參數，從不用它來產生結果。正是這條界線讓找回測試有意義；這也是為什麼 `Observations.from_csv` 回傳的資料帶有 `truth=None`，讓真實資料和合成資料走完全相同的擬合路徑。

`bayesian.py` 和 `estimation.py` 並列，而不是疊在它上面：兩個模組共用 `synthetic.Observations` 和 `estimation.PARAMETER_BOUNDS`，`run_mcmc` 也會呼叫一次 `estimate_parameters` 來決定 walker 的中心，但兩個模組都不 import 對方的結果型別。刪掉任何一個都不會讓另一個壞掉。
