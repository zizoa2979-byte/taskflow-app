import json
import os
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


def load_tasks():
    if not os.path.exists(DATA_FILE):
        tasks = [
            {"id": 1, "title": "تطوير لوحة إدارة الطلبات", "client": "منصة الهدهد", "priority": "عاجلة", "done": False},
            {"id": 2, "title": "ربط قاعدة البيانات واختبار السيرفر", "client": "نظام حجوزات", "priority": "متوسطة", "done": True},
        ]
        save_tasks(tasks)
        return tasks
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TaskFlow | إدارة مهام المشاريع</title>
  <style>
    body { font-family: Tahoma, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
    .box { max-width: 780px; margin: auto; background: #1e293b; padding: 22px; border-radius: 14px; }
    h1 { margin: 0 0 16px; font-size: 22px; }
    form { display: grid; grid-template-columns: 2fr 1.5fr 1fr auto; gap: 10px; margin-bottom: 18px; }
    input, select, button { padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #fff; }
    button { background: #0284c7; border: none; cursor: pointer; font-weight: bold; }
    .task { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 12px 14px; border-radius: 10px; margin-bottom: 10px; }
    .done { text-decoration: line-through; opacity: 0.6; }
    .actions button { margin-right: 6px; padding: 6px 10px; font-size: 12px; }
    .del { background: #dc2626; }
    @media (max-width: 680px) { form { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="box">
    <h1>TaskFlow — متابعة مهام العملاء (Python + Flask)</h1>
    <form id="f">
      <input id="title" placeholder="اسم المهمة..." required />
      <input id="client" placeholder="اسم العميل..." required />
      <select id="priority">
        <option>عاجلة</option>
        <option selected>متوسطة</option>
        <option>عادية</option>
      </select>
      <button type="submit">إضافة</button>
    </form>
    <div id="list"></div>
  </div>
  <script>
    async function load() {
      const res = await fetch("/api/tasks");
      const tasks = await res.json();
      document.getElementById("list").innerHTML = tasks.map(t => `
        <div class="task">
          <div class="${t.done ? "done" : ""}">
            <strong>${t.title}</strong> — <small>${t.client} (${t.priority})</small>
          </div>
          <div class="actions">
            <button onclick="toggle(${t.id})">${t.done ? "إلغاء" : "مكتمل"}</button>
            <button class="del" onclick="delTask(${t.id})">حذف</button>
          </div>
        </div>
      `).join("");
    }
    document.getElementById("f").onsubmit = async (e) => {
      e.preventDefault();
      await fetch("/api/tasks", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          title: title.value.trim(),
          client: client.value.trim(),
          priority: priority.value
        })
      });
      e.target.reset();
      load();
    };
    async function toggle(id) { await fetch(`/api/tasks/${id}/toggle`, {method: "PATCH"}); load(); }
    async function delTask(id) { await fetch(`/api/tasks/${id}`, {method: "DELETE"}); load(); }
    load();
  </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.get("/api/tasks")
def get_tasks():
    return jsonify(load_tasks())


@app.post("/api/tasks")
def add_task():
    d = request.get_json(silent=True) or {}
    if not d.get("title") or not d.get("client"):
        return jsonify({"error": "بيانات ناقصة"}), 400
    tasks = load_tasks()
    new_id = max([t["id"] for t in tasks], default=0) + 1
    tasks.insert(0, {
        "id": new_id,
        "title": d["title"].strip(),
        "client": d["client"].strip(),
        "priority": d.get("priority", "متوسطة"),
        "done": False,
    })
    save_tasks(tasks)
    return jsonify({"id": new_id}), 201


@app.patch("/api/tasks/<int:tid>/toggle")
def toggle_task(tid):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == tid:
            t["done"] = not t["done"]
    save_tasks(tasks)
    return jsonify({"ok": True})


@app.delete("/api/tasks/<int:tid>")
def delete_task(tid):
    tasks = [t for t in load_tasks() if t["id"] != tid]
    save_tasks(tasks)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)