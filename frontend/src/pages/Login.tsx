import { FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { login } from "../api";
import { setLang } from "../i18n";

const DEMO = ["operator", "safety", "opsmanager", "technician", "exec", "admin"];

export default function Login() {
  const { t, i18n } = useTranslation();
  const [u, setU] = useState("opsmanager");
  const [p, setP] = useState("demo1234");
  const [totp, setTotp] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      await login(u, p, totp);
    } catch (e: any) {
      setErr(String(e.message || e).slice(0, 200));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-full grid place-items-center p-4">
      <form onSubmit={submit} className="card p-6 w-full max-w-sm space-y-3">
        <div className="text-brand font-bold text-lg">INNO Terminals &amp; Tanks</div>
        <div className="text-sm text-muted">{t("app")}</div>

        <label className="block text-sm">{t("username")}
          <input className="w-full mt-1 card px-3 py-2 bg-bg" value={u}
            onChange={(e) => setU(e.target.value)} />
        </label>
        <label className="block text-sm">{t("password")}
          <input className="w-full mt-1 card px-3 py-2 bg-bg" type="password" value={p}
            onChange={(e) => setP(e.target.value)} />
        </label>
        <label className="block text-sm">{t("totp")}
          <input className="w-full mt-1 card px-3 py-2 bg-bg" value={totp}
            onChange={(e) => setTotp(e.target.value)} />
        </label>

        {err && <div className="text-red-500 text-xs">{err}</div>}
        <button className="btn btn-brand w-full" disabled={busy}>{t("login")}</button>

        <div className="text-xs text-muted pt-2">
          demo: {DEMO.join(" / ")} — pass <code>demo1234</code>
        </div>
        <button type="button" className="btn btn-ghost w-full"
          onClick={() => setLang(i18n.language === "fa" ? "en" : "fa")}>
          {i18n.language === "fa" ? "English" : "فارسی"}
        </button>
      </form>
    </div>
  );
}
