"""自动点击器 - 基于 tkinter + pyautogui 的图形化自动点击工具"""

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import pyautogui

# 禁用 pyautogui 内置保险机制，使用自定义的左上角检测代替
pyautogui.FAILSAFE = False
# 禁用 pyautogui 内置延迟，使用用户设置的间隔时间
pyautogui.PAUSE = 0


class AutoClicker:
    """自动点击器主类，封装 GUI 和点击逻辑"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("自动点击器")
        self.root.geometry("520x650")
        self.root.resizable(True, True)

        # 运行停止事件（线程间共享）
        self._stop_event = threading.Event()
        # 倒计时锁，防止重复启动
        self._countdown_running = False
        # 倒计时当前选中行
        self._countdown_target: str | None = None
        # 组后等待缓存
        self._group_wait: float = 0.0

        self._build_ui()
        # 默认添加一行
        self._add_position()

    def _build_ui(self) -> None:
        """构建 GUI 界面"""
        # 标题标签
        title_label = ttk.Label(self.root, text="自动点击器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(15, 8))

        # 位置列表区
        list_frame = ttk.LabelFrame(self.root, text="点击位置列表")
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        # Treeview + 滚动条
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(padx=8, pady=8, fill="both", expand=True)

        columns = ("idx", "x", "y", "count", "click_interval")
        self.tree = ttk.Treeview(
            tree_container, columns=columns, show="headings", height=6
        )
        self.tree.heading("idx", text="序号")
        self.tree.heading("x", text="X坐标")
        self.tree.heading("y", text="Y坐标")
        self.tree.heading("count", text="点击次数")
        self.tree.heading("click_interval", text="点击间隔(秒)")

        self.tree.column("idx", width=50, anchor="center")
        self.tree.column("x", width=80, anchor="center")
        self.tree.column("y", width=80, anchor="center")
        self.tree.column("count", width=80, anchor="center")
        self.tree.column("click_interval", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 双击编辑功能
        self.tree.bind("<Double-1>", self._on_double_click)

        # 列表操作按钮
        list_btn_frame = ttk.Frame(list_frame)
        list_btn_frame.pack(padx=8, pady=(0, 8))

        self.add_btn = ttk.Button(
            list_btn_frame, text="添加位置", command=self._add_position
        )
        self.add_btn.pack(side="left", padx=3)

        self.del_btn = ttk.Button(
            list_btn_frame, text="删除选中", command=self._delete_position
        )
        self.del_btn.pack(side="left", padx=3)

        self.get_pos_btn = ttk.Button(
            list_btn_frame, text="获取当前位置坐标", command=self._get_position_for_selected
        )
        self.get_pos_btn.pack(side="left", padx=3)

        # 全局设置区
        global_frame = ttk.LabelFrame(self.root, text="全局设置")
        global_frame.pack(padx=15, pady=5, fill="x")

        ttk.Label(global_frame, text="组后等待(秒):").grid(
            row=0, column=0, padx=10, pady=8, sticky="e"
        )
        self.group_wait_entry = ttk.Entry(global_frame, width=10)
        self.group_wait_entry.insert(0, "0")
        self.group_wait_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        ttk.Label(global_frame, text="(每个位置点完后等待几秒)").grid(
            row=0, column=2, padx=5, pady=8, sticky="w"
        )

        ttk.Label(global_frame, text="执行轮数:").grid(
            row=1, column=0, padx=10, pady=8, sticky="e"
        )
        self.rounds_entry = ttk.Entry(global_frame, width=10)
        self.rounds_entry.insert(0, "1")
        self.rounds_entry.grid(row=1, column=1, padx=5, pady=8, sticky="w")

        ttk.Label(global_frame, text="(0 表示无限循环，直到手动停止)").grid(
            row=1, column=2, padx=5, pady=8, sticky="w"
        )

        ttk.Label(global_frame, text="每轮间隔(秒):").grid(
            row=2, column=0, padx=10, pady=8, sticky="e"
        )
        self.round_interval_entry = ttk.Entry(global_frame, width=10)
        self.round_interval_entry.insert(0, "0")
        self.round_interval_entry.grid(row=2, column=1, padx=5, pady=8, sticky="w")

        ttk.Label(global_frame, text="(每轮结束后等待几秒再开始下一轮)").grid(
            row=2, column=2, padx=5, pady=8, sticky="w"
        )

        # 控制按钮区
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="开始点击", command=self.start_clicking)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ttk.Button(
            btn_frame, text="停止", command=self.stop_clicking, state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)

        # 状态标签
        self.status_label = ttk.Label(self.root, text="状态: 就绪", foreground="green")
        self.status_label.pack(pady=3)

        # 进度标签
        self.progress_label = ttk.Label(self.root, text="")
        self.progress_label.pack(pady=3)

        # 使用说明
        help_text = (
            "使用说明:\n"
            "1. 添加点击位置，双击单元格可编辑数值\n"
            "2. 选中行后点\"获取当前位置坐标\"可 3 秒后填入鼠标坐标\n"
            "3. 每个位置可独立设置点击次数和点击间隔\n"
            "4. 设置组后等待、执行轮数和每轮间隔\n"
            "5. 点击\"开始点击\"按列表顺序依次执行\n"
            "6. 点击\"停止\"或把鼠标移到屏幕左上角紧急停止"
        )
        help_label = ttk.Label(
            self.root, text=help_text, foreground="gray", justify="center",
            wraplength=480,
        )
        help_label.pack(pady=10, fill="x")

    # ------------------------------------------------------------------
    #  列表操作
    # ------------------------------------------------------------------

    def _add_position(self) -> None:
        """在列表末尾添加一行新位置（默认值）"""
        items = self.tree.get_children()
        idx = len(items) + 1
        self.tree.insert("", "end", values=(idx, 0, 0, 1, 0.5))

    def _delete_position(self) -> None:
        """删除选中的行"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的行")
            return
        for item in selected:
            self.tree.delete(item)
        # 重新编号
        self._renumber_items()

    def _renumber_items(self) -> None:
        """重新编号所有行的序号列"""
        items = self.tree.get_children()
        for i, item in enumerate(items, start=1):
            vals = list(self.tree.item(item, "values"))
            vals[0] = i
            self.tree.item(item, values=vals)

    def _on_double_click(self, event: tk.Event) -> None:
        """双击单元格进入编辑模式"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item or not column:
            return

        col_idx = int(column.replace("#", "")) - 1
        # 序号列不可编辑
        if col_idx == 0:
            return

        x, y, w, h = self.tree.bbox(item, column)
        current_val = self.tree.set(item, column)

        entry = ttk.Entry(self.tree, width=max(w // 8, 3), justify="center")
        entry.insert(0, current_val)
        entry.select_range(0, tk.END)
        entry.focus()
        entry.place(x=x, y=y, width=w, height=h)

        def _save(_e: tk.Event | None = None) -> None:
            new_val = entry.get().strip()
            if new_val == "":
                new_val = "0"
            vals = list(self.tree.item(item, "values"))
            vals[col_idx] = new_val
            self.tree.item(item, values=vals)
            entry.destroy()

        def _cancel(_e: tk.Event | None = None) -> None:
            entry.destroy()

        entry.bind("<Return>", _save)
        entry.bind("<FocusOut>", _save)
        entry.bind("<Escape>", _cancel)

    # ------------------------------------------------------------------
    #  倒计时 - 获取鼠标位置（选中行）
    # ------------------------------------------------------------------

    def _get_position_for_selected(self) -> None:
        """对选中行启动 3 秒倒计时获取坐标"""
        if self._countdown_running:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一行再获取坐标")
            return
        self._countdown_running = True
        self._countdown_target = selected[0]
        self.get_pos_btn.config(state="disabled")
        threading.Thread(target=self._countdown_worker, daemon=True).start()

    def _countdown_worker(self) -> None:
        """倒计时工作线程，每秒更新按钮文字"""
        try:
            for remaining in range(3, 0, -1):
                self.root.after(0, lambda r=remaining: self.get_pos_btn.config(
                    text=f"{r}秒后获取..."
                ))
                time.sleep(1)

            # 倒计时结束，获取坐标
            pos_x, pos_y = pyautogui.position()
            target = self._countdown_target

            def _update_coord() -> None:
                if target in self.tree.get_children():
                    vals = list(self.tree.item(target, "values"))
                    vals[1] = pos_x  # X
                    vals[2] = pos_y  # Y
                    self.tree.item(target, values=vals)
                self.get_pos_btn.config(state="normal", text="获取当前位置坐标")
                self._countdown_running = False
                self._countdown_target = None

            self.root.after(0, _update_coord)
        except Exception as e:
            self._countdown_running = False
            self._countdown_target = None

            def _error_handler(err: Exception = e) -> None:
                self.get_pos_btn.config(state="normal", text="获取当前位置坐标")
                messagebox.showerror("获取坐标失败", str(err))

            self.root.after(0, _error_handler)

    # ------------------------------------------------------------------
    #  输入验证
    # ------------------------------------------------------------------

    def _validate_and_get_click_plan(
        self,
    ) -> tuple[list[tuple[int, int, int, float]], float, int, float] | None:
        """
        读取列表所有行，验证数据，返回点击计划及全局参数。
        返回: (click_plan, group_wait, total_rounds, round_interval)
        验证失败返回 None 并弹错误提示。
        """
        items = self.tree.get_children()
        if not items:
            messagebox.showerror("输入错误", "至少需要一个点击位置")
            return None

        # 组后等待
        try:
            group_wait = float(self.group_wait_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "组后等待必须是数字")
            return None
        if group_wait < 0:
            messagebox.showerror("输入错误", "组后等待不能小于 0")
            return None

        # 执行轮数
        try:
            total_rounds = int(self.rounds_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "执行轮数必须是整数")
            return None
        if total_rounds < 0:
            messagebox.showerror("输入错误", "执行轮数不能小于 0（0 表示无限）")
            return None

        # 每轮间隔
        try:
            round_interval = float(self.round_interval_entry.get())
        except ValueError:
            messagebox.showerror("输入错误", "每轮间隔必须是数字")
            return None
        if round_interval < 0:
            messagebox.showerror("输入错误", "每轮间隔不能小于 0")
            return None

        plan: list[tuple[int, int, int, float]] = []
        for i, item in enumerate(items, start=1):
            vals = self.tree.item(item, "values")
            # X 坐标
            try:
                x_val = int(vals[1])
            except ValueError:
                messagebox.showerror("输入错误", f"第 {i} 行 X 坐标必须是整数")
                return None
            # Y 坐标
            try:
                y_val = int(vals[2])
            except ValueError:
                messagebox.showerror("输入错误", f"第 {i} 行 Y 坐标必须是整数")
                return None
            # 点击次数
            try:
                count_val = int(vals[3])
            except ValueError:
                messagebox.showerror("输入错误", f"第 {i} 行 点击次数必须是整数")
                return None
            if count_val <= 0:
                messagebox.showerror("输入错误", f"第 {i} 行 点击次数必须大于 0")
                return None
            # 点击间隔
            try:
                click_interval = float(vals[4])
            except ValueError:
                messagebox.showerror("输入错误", f"第 {i} 行 点击间隔必须是数字")
                return None
            if click_interval < 0:
                messagebox.showerror("输入错误", f"第 {i} 行 点击间隔不能小于 0")
                return None

            plan.append((x_val, y_val, count_val, click_interval))

        self._group_wait = group_wait
        return plan, group_wait, total_rounds, round_interval

    # ------------------------------------------------------------------
    #  开始 / 停止
    # ------------------------------------------------------------------

    def start_clicking(self) -> None:
        """开始点击按钮回调"""
        result = self._validate_and_get_click_plan()
        if result is None:
            return
        plan, group_wait, total_rounds, round_interval = result

        self._stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.add_btn.config(state="disabled")
        self.del_btn.config(state="disabled")
        self.get_pos_btn.config(state="disabled")
        self.status_label.config(text="状态: 运行中...", foreground="blue")
        first_count = plan[0][2]
        rounds_label = f"共 {total_rounds} 轮" if total_rounds > 0 else "无限"
        self.progress_label.config(
            text=f"第 1 轮 / {rounds_label} - 位置 1/{len(plan)} - 第 0/{first_count} 次"
        )

        threading.Thread(
            target=self.click_loop,
            args=(plan, group_wait, total_rounds, round_interval),
            daemon=True,
        ).start()

    def stop_clicking(self) -> None:
        """停止点击。可从主线程或工作线程调用。"""
        self._stop_event.set()
        try:
            if threading.current_thread() is threading.main_thread():
                self._reset_ui()
            else:
                self.root.after(0, self._reset_ui)
        except RuntimeError:
            self.root.after(0, self._reset_ui)

    def _reset_ui(self) -> None:
        """重置界面到初始状态（主线程执行）"""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.add_btn.config(state="normal")
        self.del_btn.config(state="normal")
        self.get_pos_btn.config(state="normal", text="获取当前位置坐标")
        self.status_label.config(text="状态: 就绪", foreground="green")
        self.progress_label.config(text="")

    # ------------------------------------------------------------------
    #  点击循环（后台线程）
    # ------------------------------------------------------------------

    def click_loop(
        self,
        click_plan: list[tuple[int, int, int, float]],
        group_wait: float,
        total_rounds: int,
        round_interval: float,
    ) -> None:
        """
        后台点击循环，按列表顺序依次执行每个位置，支持多轮循环。
        group_wait: 每个位置点完后的组后等待（全局设置）
        total_rounds: 总轮数，0 表示无限循环
        round_interval: 每轮间隔（秒）
        所有 UI 更新都通过 root.after(0, ...) 调度到主线程。
        """
        try:
            total_positions = len(click_plan)
            total_clicks = sum(c for _, _, c, _ in click_plan)

            rounds_text = f"共 {total_rounds} 轮" if total_rounds > 0 else "无限"
            completed_rounds = 0
            round_num = 0

            while True:
                round_num += 1

                # 如果不是无限循环且已超过总轮数，退出
                if total_rounds > 0 and round_num > total_rounds:
                    break

                # 执行一轮所有位置
                for pos_idx, (x_val, y_val, count_val, click_interval) in enumerate(
                    click_plan, start=1
                ):
                    # 每个位置的点击循环
                    for click_idx in range(1, count_val + 1):
                        # 检查停止标志
                        if self._stop_event.is_set():
                            return

                        # 紧急停止检测：鼠标移到左上角 (x<10 且 y<10)
                        mx, my = pyautogui.position()
                        if mx < 10 and my < 10:
                            self._stop_event.set()

                            def _emergency_stop() -> None:
                                self._reset_ui()
                                messagebox.showwarning(
                                    "紧急停止", "检测到鼠标在左上角，已紧急停止！"
                                )

                            self.root.after(0, _emergency_stop)
                            return

                        # 执行左键单击
                        pyautogui.click(x_val, y_val)

                        # 更新进度
                        rn, pi, ci = round_num, pos_idx, click_idx
                        self.root.after(
                            0,
                            lambda r=rn, p=pi, c=ci, rt=rounds_text, total=total_positions, cnt=count_val: (
                                self.progress_label.config(
                                    text=f"第 {r} 轮 / {rt} - 位置 {p}/{total} - 第 {c}/{cnt} 次"
                                )
                            ),
                        )

                        # 等待间隔（同一位置内多次点击之间，不是最后一次才等）
                        if click_idx < count_val and click_interval > 0:
                            time.sleep(click_interval)

                        if self._stop_event.is_set():
                            return

                    # 组后等待（不是最后一个位置才等）
                    if pos_idx < total_positions and group_wait > 0:
                        if self._stop_event.is_set():
                            return
                        time.sleep(group_wait)

                completed_rounds = round_num

                # 每轮结束后等待（不是最后一轮才等，无限循环时每轮后都等）
                is_last_round = total_rounds > 0 and round_num >= total_rounds
                if round_interval > 0 and not is_last_round:
                    if self._stop_event.is_set():
                        return
                    time.sleep(round_interval)

                # 检查停止
                if self._stop_event.is_set():
                    return

            # 正常结束（仅有限轮数会走到这里）
            if not self._stop_event.is_set():
                self._stop_event.set()

                def _finish(
                    rounds_done: int = completed_rounds,
                    positions: int = total_positions,
                    clicks: int = total_clicks,
                ) -> None:
                    self._reset_ui()
                    messagebox.showinfo(
                        "完成",
                        f"已完成 {rounds_done} 轮，共 {positions} 个位置，{rounds_done * clicks} 次点击！",
                    )

                self.root.after(0, _finish)
        except Exception as e:
            self._stop_event.set()

            def _error_handler(err: Exception = e) -> None:
                self._reset_ui()
                messagebox.showerror("运行错误", str(err))

            self.root.after(0, _error_handler)


def main() -> None:
    root = tk.Tk()
    AutoClicker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
