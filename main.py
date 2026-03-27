import sys
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget, QLineEdit, QFormLayout, 
    QComboBox, QDateEdit, QFrame, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QFileDialog, QRadioButton, QButtonGroup, QGraphicsDropShadowEffect,
    QScrollArea, QGridLayout, QCheckBox
)
from PySide6.QtCore import QDate, Qt, QSize
from PySide6.QtGui import QColor, QFont, QPixmap
from security import verify_and_unlock
from styles import MAIN_STYLE

def apply_shadow(widget, is_login=False):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(40)
    shadow.setColor(QColor(17, 28, 45, 15)) 
    shadow.setOffset(0, 20)
    if is_login:
        shadow.setColor(QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(shadow)

# Custom Bento Card Generator
def create_kpi_card(title, value, accent_color=None):
    card = QFrame()
    card.setProperty("class", "KPICard")
    apply_shadow(card)
    card.setMinimumHeight(120)
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(25, 25, 25, 25)
    
    lbl_title = QLabel(title)
    lbl_title.setProperty("class", "KPILabel")
    
    lbl_value = QLabel(str(value))
    lbl_value.setProperty("class", "KPIValue")
    if accent_color:
        lbl_value.setStyleSheet(f"color: {accent_color};")
        
    card_layout.addWidget(lbl_title)
    card_layout.addWidget(lbl_value)
    card_layout.addStretch()
    return card, lbl_value


class OverviewWidget(QWidget):
    def __init__(self, db_conn):
        super().__init__()
        self.db = db_conn
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)
        
        cursor = self.db.cursor()
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_workforce = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status IN ('Present', 'Half-Day')", (today_str,))
        present_today = cursor.fetchone()[0]
        attendance_rate = f"{(present_today / total_workforce * 100):.1f}%" if total_workforce > 0 else "0.0%"
        
        cursor.execute("SELECT id, base_salary FROM employees")
        emps = cursor.fetchall()
        total_liability = 0
        current_month = QDate.currentDate().toString("yyyy-MM")
        for emp_id, base_sal in emps:
            cursor.execute("SELECT status FROM attendance WHERE employee_id=? AND date LIKE ?", (emp_id, f"{current_month}-%"))
            records = cursor.fetchall()
            days_present = sum(1 for r in records if r[0] == "Present")
            half_days = sum(0.5 for r in records if r[0] == "Half-Day")
            total_liability += (base_sal / 30.0) * (days_present + half_days)
        liability_str = f"₹{total_liability:,.2f}"
        
        cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM attendance WHERE date=?", (today_str,))
        marked_today = cursor.fetchone()[0]
        pending_approvals = max(0, total_workforce - marked_today)
        
        # 1. Top KPI Row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(20)
        
        card1 = self.create_kpi_card("TOTAL WORKFORCE", f"{total_workforce:,}", "↗ +4.2%" if total_workforce > 0 else None, "#10b981")
        card2 = self.create_kpi_card("ATTENDANCE RATE\n(TODAY)", attendance_rate, "bar" if total_workforce > 0 else None, "#10b981")
        card3 = self.create_kpi_card("MONTHLY PAYROLL\nLIABILITY", liability_str, None, None)
        
        card4 = QFrame()
        card4.setStyleSheet("background-color: #fee2e2; border-radius: 12px;")
        apply_shadow(card4)
        card4.setFixedSize(220, 110)
        l4 = QVBoxLayout(card4)
        t4 = QLabel("PENDING APPROVALS")
        t4.setStyleSheet("color: #9f1239; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        val_ly = QHBoxLayout()
        v4 = QLabel(str(pending_approvals))
        v4.setStyleSheet("color: #9f1239; font-size: 32px; font-weight: 900;")
        if pending_approvals > 0:
            badge = QLabel("CRITICAL")
            badge.setStyleSheet("background-color: #e11d48; color: white; padding: 4px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;")
            val_ly.addWidget(v4)
            val_ly.addWidget(badge, alignment=Qt.AlignRight | Qt.AlignVCenter)
        else:
            val_ly.addWidget(v4)
        l4.addWidget(t4)
        l4.addLayout(val_ly)
        
        kpi_row.addWidget(card1)
        kpi_row.addWidget(card2)
        kpi_row.addWidget(card3)
        kpi_row.addWidget(card4)
        kpi_row.addStretch()
        
        main_layout.addLayout(kpi_row)
        
        # 2. Middle Row
        mid_row = QHBoxLayout()
        mid_row.setSpacing(20)
        
        trends_card = QFrame()
        trends_card.setProperty("class", "KPICard")
        apply_shadow(trends_card)
        trends_layout = QVBoxLayout(trends_card)
        
        trend_header = QHBoxLayout()
        th = QLabel("Attendance Trends<br><span style='font-size: 12px; color: #8590a6; font-weight: normal;'>Daily workforce participation over 14 days</span>")
        th.setTextFormat(Qt.RichText)
        th.setStyleSheet("font-size: 18px; font-weight: bold; color: #111c2d;")
        pill = QLabel("Last 14 Days")
        pill.setStyleSheet("background-color: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;")
        trend_header.addWidget(th)
        trend_header.addStretch()
        trend_header.addWidget(pill, alignment=Qt.AlignTop)
        trends_layout.addLayout(trend_header)
        
        chart_layout = QHBoxLayout()
        chart_layout.setContentsMargins(10, 20, 10, 10)
        chart_layout.setSpacing(8)
        max_h = 80
        for i in range(13, -1, -1):
            d = QDate.currentDate().addDays(-i).toString("yyyy-MM-dd")
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status IN ('Present', 'Half-Day')", (d,))
            cnt = cursor.fetchone()[0]
            
            h = int((cnt / total_workforce * max_h)) if total_workforce > 0 else 0
            h = max(4, h)
            
            bar_container = QVBoxLayout()
            bar = QFrame()
            bar.setFixedSize(24, h)
            if i == 0:
                bar.setStyleSheet("background-color: #0058be; border-radius: 4px;")
            else:
                bar.setStyleSheet("background-color: #bfdbfe; border-radius: 4px;")
            bar_container.addStretch()
            bar_container.addWidget(bar)
            chart_layout.addLayout(bar_container)
        
        trends_layout.addLayout(chart_layout)
        
        tfooter = QHBoxLayout()
        tfooter.addWidget(QLabel("<span style='color: #8590a6; font-size: 10px; font-weight: bold; letter-spacing: 1px;'>DAY 01</span>"))
        tfooter.addStretch()
        tfooter.addWidget(QLabel("<span style='color: #8590a6; font-size: 10px; font-weight: bold; letter-spacing: 1px;'>DAY 07</span>"))
        tfooter.addStretch()
        tfooter.addWidget(QLabel("<span style='color: #8590a6; font-size: 10px; font-weight: bold; letter-spacing: 1px;'>TODAY</span>"))
        trends_layout.addLayout(tfooter)
        
        desig_card = QFrame()
        desig_card.setStyleSheet("background-color: #0f172a; border-radius: 12px;")
        apply_shadow(desig_card)
        desig_card.setFixedWidth(300)
        dl = QVBoxLayout(desig_card)
        dl.setContentsMargins(24, 24, 24, 24)
        dl_title = QLabel("Designation Breakdown")
        dl_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        dl.addWidget(dl_title)
        
        cursor.execute("SELECT designation, COUNT(*) FROM employees GROUP BY designation ORDER BY COUNT(*) DESC LIMIT 5")
        desigs = cursor.fetchall()
        colors = ["#34d399", "#60a5fa", "#f472b6", "#fbbf24", "#a78bfa"]
        if not desigs:
            bl = QLabel("No Data Available")
            bl.setStyleSheet("color: #64748b; font-style: italic;")
            dl.addWidget(bl)
        for i, (name, count) in enumerate(desigs):
            color = colors[i % len(colors)]
            r = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            lbl = QLabel(name if name else "Unassigned")
            lbl.setStyleSheet("color: white; font-size: 13px; font-weight: 500;")
            val = QLabel(str(count))
            val.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
            r.addWidget(dot)
            r.addWidget(lbl)
            r.addStretch()
            r.addWidget(val)
            dl.addLayout(r)
            
        dl.addStretch()
        
        mid_row.addWidget(trends_card, stretch=7)
        mid_row.addWidget(desig_card, stretch=3)
        main_layout.addLayout(mid_row)
        
        # 3. Bottom Row
        bot_row = QHBoxLayout()
        bot_row.setSpacing(20)
        
        feed_card = QFrame()
        feed_card.setProperty("class", "KPICard")
        apply_shadow(feed_card)
        fl = QVBoxLayout(feed_card)
        tf = QLabel("Recent Activity Feed")
        tf.setStyleSheet("font-size: 18px; font-weight: bold; color: #111c2d; margin-bottom: 10px;")
        fl.addWidget(tf)
        
        def create_feed_item(icon_text, icon_color, icon_bg, title, subtitle):
            r = QHBoxLayout()
            icon = QLabel(icon_text)
            icon.setAlignment(Qt.AlignCenter)
            icon.setFixedSize(36, 36)
            icon.setStyleSheet(f"background-color: {icon_bg}; color: {icon_color}; border-radius: 18px; font-weight: bold; font-size: 16px;")
            vl = QVBoxLayout()
            vl.setSpacing(2)
            t = QLabel(title)
            t.setStyleSheet("font-size: 13px; color: #111c2d;")
            t.setTextFormat(Qt.RichText)
            s = QLabel(subtitle)
            s.setStyleSheet("font-size: 11px; color: #64748b;")
            vl.addWidget(t)
            vl.addWidget(s)
            r.addWidget(icon)
            r.addLayout(vl)
            r.addStretch()
            return r
            
        cursor.execute("SELECT name, designation, id FROM employees ORDER BY id DESC LIMIT 3")
        recent_emps = cursor.fetchall()
        if not recent_emps:
            fl.addWidget(QLabel("No recent activity found."))
        else:
            for idx, (name, desig, eid) in enumerate(recent_emps):
                fl.addLayout(create_feed_item("👤", "#1e40af", "#dbeafe", f"<b>New Employee Added:</b> {name}", f"ID: {eid} • {desig if desig else 'Unassigned'}"))
                fl.addSpacing(15)
        
        fl.addStretch()
        
        quick_layout = QVBoxLayout()
        quick_title = QLabel("QUICK MANAGEMENT")
        quick_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        
        def create_qbtn(text, is_primary=False):
            b = QPushButton(text)
            if is_primary:
                b.setStyleSheet("""
                    QPushButton { background-color: #0058be; color: white; border-radius: 8px; font-weight: bold; text-align: left; padding: 16px; font-size: 13px; }
                    QPushButton:hover { background-color: #2170e4; }
                """)
            else:
                b.setStyleSheet("""
                    QPushButton { background-color: #e2e8f0; color: #0f172a; border-radius: 8px; font-weight: bold; text-align: left; padding: 16px; font-size: 13px; }
                    QPushButton:hover { background-color: #cbd5e1; }
                """)
            return b
            
        quick_layout.addWidget(quick_title)
        q1 = create_qbtn("💳 Run Payroll", True)
        q2 = create_qbtn("📄 Export Attendance")
        q3 = create_qbtn("➕ Add New Record")
        q4 = create_qbtn("🛡️ System Security Audit")
        quick_layout.addWidget(q1)
        quick_layout.addWidget(q2)
        quick_layout.addWidget(q3)
        quick_layout.addWidget(q4)
        quick_layout.addStretch()
        
        bot_row.addWidget(feed_card, stretch=7)
        bot_row.addLayout(quick_layout, stretch=3)
        main_layout.addLayout(bot_row)
        
    def create_kpi_card(self, title, val, diff, diff_color="#000000"):
        card = QFrame()
        card.setProperty("class", "KPICard")
        apply_shadow(card)
        card.setFixedSize(220, 110)
        ly = QVBoxLayout(card)
        t = QLabel(title)
        t.setProperty("class", "KPILabel")
        v = QLabel(val)
        v.setProperty("class", "KPIValue")
        v.setStyleSheet("font-size: 28px;") 
        ly.addWidget(t)
        bot = QHBoxLayout()
        bot.addWidget(v)
        if diff:
            if diff == "bar":
                bar = QFrame()
                bar.setFixedSize(60, 6)
                bar.setStyleSheet("background-color: #34d399; border-radius: 3px;")
                bot.addWidget(bar, alignment=Qt.AlignRight | Qt.AlignVCenter)
            else:
                dl = QLabel(diff)
                dl.setStyleSheet(f"color: {diff_color}; font-size: 12px; font-weight: bold;")
                bot.addWidget(dl, alignment=Qt.AlignRight | Qt.AlignVCenter)
        else:
            bot.addStretch()
        ly.addLayout(bot)
        return card

class AddEmployeeWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        header_layout = QVBoxLayout()
        title = QLabel("Personnel Registry")
        title.setProperty("class", "TitleLabel")
        subtitle = QLabel("Management and deployment of organizational assets.")
        subtitle.setProperty("class", "SubtitleLabel")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        split_layout = QHBoxLayout()
        split_layout.setSpacing(30)
        
        # LEFT PANEL: Add Employee Form
        left_panel = QFrame()
        left_panel.setProperty("class", "CardWidget")
        apply_shadow(left_panel)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(35, 35, 35, 35)
        left_layout.setSpacing(15)
        
        form_title = QLabel("Add New Employee")
        form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #091426;")
        left_layout.addWidget(form_title)
        left_layout.addSpacing(10)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Alistair Vance")
        
        self.salary_input = QLineEdit()
        self.salary_input.setPlaceholderText("0.00")
        
        self.designation_input = QComboBox()
        self.designation_input.addItems(["Select Role", "Architect", "Project Lead", "Driver", "Analyst"])
        self.designation_input.currentTextChanged.connect(self.toggle_driver_fields)
        
        self.vehicle_no_input = QLineEdit()
        self.vehicle_no_input.setPlaceholderText("XYZ-9082")
        
        self.vehicle_type_input = QLineEdit()
        self.vehicle_type_input.setPlaceholderText("Heavy Cargo")
        
        self.license_no_input = QLineEdit()
        self.license_no_input.setPlaceholderText("DL-XXXX-XXXX")
        
        form_layout.addRow(QLabel("Full Name:"), self.name_input)
        form_layout.addRow(QLabel("Base Salary:"), self.salary_input)
        form_layout.addRow(QLabel("Designation:"), self.designation_input)
        
        self.driver_label_1 = QLabel("Veh No:")
        self.driver_label_2 = QLabel("Veh Type:")
        self.driver_label_3 = QLabel("License:")
        
        form_layout.addRow(self.driver_label_1, self.vehicle_no_input)
        form_layout.addRow(self.driver_label_2, self.vehicle_type_input)
        form_layout.addRow(self.driver_label_3, self.license_no_input)
        left_layout.addLayout(form_layout)
        
        left_layout.addStretch()
        self.submit_btn = QPushButton("Save Employee Record")
        self.submit_btn.setProperty("class", "PrimaryButton")
        self.submit_btn.clicked.connect(self.save_employee)
        left_layout.addWidget(self.submit_btn)
        
        # RIGHT PANEL: Recent Additions Table
        right_panel = QFrame()
        right_panel.setProperty("class", "CardWidget")
        apply_shadow(right_panel)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        header_table = QLabel("Recently Added")
        header_table.setStyleSheet("font-size: 18px; font-weight: bold; color: #091426; padding: 25px 25px 10px 25px;")
        right_layout.addWidget(header_table)
        
        self.recent_table = QTableWidget(0, 3)
        self.recent_table.setHorizontalHeaderLabels(["Employee Name", "Role", "Base Salary"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.setFocusPolicy(Qt.NoFocus)
        right_layout.addWidget(self.recent_table)
        
        split_layout.addWidget(left_panel, stretch=2)
        split_layout.addWidget(right_panel, stretch=3)
        
        main_layout.addLayout(split_layout)
        self.toggle_driver_fields("Select Role")
        self.refresh_recent()

    def refresh_recent(self):
        self.recent_table.setRowCount(0)
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT name, designation, base_salary FROM employees ORDER BY id DESC LIMIT 20")
            for row_idx, row in enumerate(cursor.fetchall()):
                self.recent_table.insertRow(row_idx)
                self.recent_table.setItem(row_idx, 0, QTableWidgetItem(str(row[0])))
                self.recent_table.setItem(row_idx, 1, QTableWidgetItem(str(row[1])))
                self.recent_table.setItem(row_idx, 2, QTableWidgetItem(f"₹{row[2]:.2f}"))
        except Exception as e:
            print("Error loading recent employees:", e)

    def toggle_driver_fields(self, designation):
        is_driver = (designation == "Driver")
        self.driver_label_1.setVisible(is_driver)
        self.driver_label_2.setVisible(is_driver)
        self.driver_label_3.setVisible(is_driver)
        self.vehicle_no_input.setVisible(is_driver)
        self.vehicle_type_input.setVisible(is_driver)
        self.license_no_input.setVisible(is_driver)

    def save_employee(self):
        name = self.name_input.text()
        salary = self.salary_input.text()
        designation = self.designation_input.currentText()
        if designation == "Select Role": designation = "Staff"
        
        veh_no = self.vehicle_no_input.text() if designation == "Driver" else ""
        veh_type = self.vehicle_type_input.text() if designation == "Driver" else ""
        lic_no = self.license_no_input.text() if designation == "Driver" else ""
        
        if not name or not salary:
            QMessageBox.warning(self, "Error", "Name and Salary are required.")
            return
            
        try:
            salary_val = float(salary)
            cursor = self.db.cursor()
            cursor.execute(
                "INSERT INTO employees (name, base_salary, designation, vehicle_number, vehicle_type, license_number) VALUES (?, ?, ?, ?, ?, ?)", 
                (name, salary_val, designation, veh_no, veh_type, lic_no)
            )
            self.db.commit()
            self.name_input.clear()
            self.salary_input.clear()
            self.vehicle_no_input.clear()
            self.vehicle_type_input.clear()
            self.license_no_input.clear()
            self.refresh_recent()
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Base salary must be a valid number.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))


class MarkAttendanceWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.init_ui()

    def update_kpis(self):
        date_str = self.date_picker.date().toString(Qt.ISODate)
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'Present'", (date_str,))
            present_c = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND status = 'Absent'", (date_str,))
            absent_c = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM employees")
            total_e = cursor.fetchone()[0]
            
            self.lbl_present.setText(str(present_c))
            self.lbl_absent.setText(str(absent_c))
            perc = 0
            if total_e > 0:
                perc = round(((present_c + absent_c) / total_e) * 100)
            self.lbl_completion.setText(f"{perc}%")
        except Exception as e:
            print("Error updating KPIs:", e)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        header_layout = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Mark Attendance")
        title.setProperty("class", "TitleLabel")
        subtitle = QLabel("Real-time daily roster management for the enterprise workforce.")
        subtitle.setProperty("class", "SubtitleLabel")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header_layout.addLayout(titles)
        
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.dateChanged.connect(self.refresh_grid)
        header_layout.addStretch()
        header_layout.addWidget(self.date_picker)
        
        main_layout.addLayout(header_layout)
        
        # KPI Cards Row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        card1, self.lbl_present = create_kpi_card("Total Present", "0", accent_color="#091426")
        card2, self.lbl_absent = create_kpi_card("Total Absent", "0", accent_color="#ba1a1a")
        card3, self.lbl_completion = create_kpi_card("Batch Completion Matrix", "0%", accent_color="#4edea3")
        card3.setStyleSheet("background-color: #091426;")
        self.lbl_completion.setStyleSheet("color: #4edea3; font-size: 38px; font-weight: 900;")
        
        kpi_layout.addWidget(card1, stretch=1)
        kpi_layout.addWidget(card2, stretch=1)
        kpi_layout.addWidget(card3, stretch=2)
        main_layout.addLayout(kpi_layout)
        
        main_layout.addSpacing(15)
        
        # Scroll Area Grid substituting Table
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_layout.setSpacing(8)
        self.scroll_area.setWidget(self.grid_widget)
        
        grid_container = QFrame()
        grid_container.setProperty("class", "CardWidget")
        apply_shadow(grid_container)
        g_layout = QVBoxLayout(grid_container)
        g_layout.setContentsMargins(10, 10, 10, 10)
        
        # Grid Header
        h_row = QHBoxLayout()
        h_row.setContentsMargins(20, 10, 20, 10)
        h1 = QLabel("Employee Profile"); h1.setProperty("class", "KPILabel")
        h2 = QLabel("Designation"); h2.setProperty("class", "KPILabel")
        h3 = QLabel("Attendance Action"); h3.setProperty("class", "KPILabel")
        h_row.addWidget(h1, stretch=3)
        h_row.addWidget(h2, stretch=2)
        h_row.addWidget(h3, stretch=2, alignment=Qt.AlignRight)
        g_layout.addLayout(h_row)
        g_layout.addWidget(self.scroll_area)
        
        main_layout.addWidget(grid_container)
        self.refresh_grid()

    def refresh_grid(self):
        # Clear layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        date_str = self.date_picker.date().toString(Qt.ISODate)
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT id, name, designation FROM employees")
            employees = cursor.fetchall()
            
            for emp_id, name, designation in employees:
                # Check current status
                cursor.execute("SELECT status FROM attendance WHERE employee_id = ? AND date = ?", (emp_id, date_str))
                status_row = cursor.fetchone()
                current_status = status_row[0] if status_row else None
                
                row = QFrame()
                row.setStyleSheet("background-color: #f9f9ff; border-radius: 8px; margin: 2px;")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(20, 15, 20, 15)
                
                # Col 1: Profile
                prof_layout = QVBoxLayout()
                prof_layout.setSpacing(2)
                lbl_name = QLabel(name)
                lbl_name.setStyleSheet("font-weight: bold; color: #091426; font-size: 14px;")
                lbl_tag = QLabel(f"EMP-{emp_id:04d}")
                lbl_tag.setStyleSheet("font-size: 11px; color: #8590a6;")
                prof_layout.addWidget(lbl_name)
                prof_layout.addWidget(lbl_tag)
                row_layout.addLayout(prof_layout, stretch=3)
                
                # Col 2: Badge
                desig_str = str(designation) if designation else "Staff"
                lbl_desig = QLabel(desig_str)
                lbl_desig.setProperty("class", "BadgeDesignation")
                lbl_desig.setAlignment(Qt.AlignCenter)
                lbl_desig.setFixedSize(120, 24)
                
                desig_layout = QHBoxLayout()
                desig_layout.addWidget(lbl_desig)
                desig_layout.addStretch()
                row_layout.addLayout(desig_layout, stretch=2)
                
                # Col 3: Actions
                actions = QHBoxLayout()
                btn_present = QPushButton("Present")
                btn_absent = QPushButton("Absent")
                btn_half = QPushButton("Half-Day")
                
                for btn in [btn_present, btn_absent, btn_half]:
                    btn.setProperty("class", "AttendanceActionBtn")
                    btn.setFixedSize(70, 30)
                
                # Highlight active status
                if current_status == "Present":
                    btn_present.setStyleSheet("background-color: #4edea3; color: #00301e; border:none; font-weight: bold;")
                elif current_status == "Absent":
                    btn_absent.setStyleSheet("background-color: #ffdad6; color: #ba1a1a; border:none; font-weight: bold;")
                elif current_status == "Half-Day":
                    btn_half.setStyleSheet("background-color: #fcebc5; color: #9c6c0b; border:none; font-weight: bold;")
                
                # Lambdas to bind specific emp and status
                btn_present.clicked.connect(lambda checked, e=emp_id, s="Present": self.mark_status(e, s))
                btn_absent.clicked.connect(lambda checked, e=emp_id, s="Absent": self.mark_status(e, s))
                btn_half.clicked.connect(lambda checked, e=emp_id, s="Half-Day": self.mark_status(e, s))
                
                actions.addWidget(btn_present)
                actions.addWidget(btn_absent)
                actions.addWidget(btn_half)
                row_layout.addLayout(actions, stretch=2)
                
                self.grid_layout.addWidget(row)
                
            self.update_kpis()
        except Exception as e:
            print("Error generating grid:", e)

    def mark_status(self, emp_id, status):
        date_str = self.date_picker.date().toString(Qt.ISODate)
        try:
            cursor = self.db.cursor()
            # Upsert logic (Delete if exists, then Insert)
            cursor.execute("DELETE FROM attendance WHERE employee_id = ? AND date = ?", (emp_id, date_str))
            cursor.execute("INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)", (emp_id, date_str, status))
            self.db.commit()
            self.refresh_grid()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))


class PayslipWidget(QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.payslip_data = []
        self.init_ui()

    def refresh_employees(self):
        self.employee_dropdown.clear()
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT id, name FROM employees")
            for row in cursor.fetchall():
                self.employee_dropdown.addItem(row[1], row[0])
        except Exception as e:
            print("Error loading employees:", e)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        header_layout = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Payroll Processing")
        title.setProperty("class", "TitleLabel")
        self.subtitle = QLabel("Financial ledger routing matrix.")
        self.subtitle.setProperty("class", "SubtitleLabel")
        titles.addWidget(title)
        titles.addWidget(self.subtitle)
        header_layout.addLayout(titles)
        
        self.gen_btn_top = QPushButton("Generate Matrix")
        self.gen_btn_top.setProperty("class", "SuccessButton")
        self.gen_btn_top.clicked.connect(self.calculate_payslips)
        header_layout.addStretch()
        header_layout.addWidget(self.gen_btn_top)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(15)
        
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.card_1, self.lbl_liability = create_kpi_card("Total Payroll Liability", "₹0.00", accent_color="#091426")
        self.card_2, self.lbl_paid = create_kpi_card("Total Employees Processed", "0", accent_color="#0058be")
        
        kpi_layout.addWidget(self.card_1)
        kpi_layout.addWidget(self.card_2)
        main_layout.addLayout(kpi_layout)
        
        main_layout.addSpacing(20)
        
        controls = QFrame()
        controls.setProperty("class", "CardWidget")
        controls.setStyleSheet("border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; background-color: #ffffff;")
        apply_shadow(controls)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(20, 15, 20, 15)
        
        self.radio_bulk = QRadioButton("Bulk Matrix")
        self.radio_bulk.setChecked(True)
        self.radio_single = QRadioButton("Individual Ledger")
        self.mode_group = QButtonGroup(); self.mode_group.addButton(self.radio_bulk); self.mode_group.addButton(self.radio_single)
        
        self.month_picker = QDateEdit()
        self.month_picker.setDisplayFormat("MM/yyyy")
        self.month_picker.setDate(QDate.currentDate())
        self.month_picker.dateChanged.connect(self.update_subtitle)
        self.update_subtitle()
        
        self.employee_dropdown = QComboBox()
        self.employee_dropdown.setFixedWidth(200)
        self.employee_dropdown.setVisible(False)
        self.radio_bulk.toggled.connect(self.toggle_mode)
        
        self.pdf_btn = QPushButton("Export PDF")
        self.pdf_btn.setProperty("class", "DangerButton")
        self.pdf_btn.clicked.connect(self.export_pdf)
        
        self.excel_btn = QPushButton("Export Excel")
        self.excel_btn.setProperty("class", "GhostButton")
        self.excel_btn.clicked.connect(self.export_excel)
        
        controls_layout.addWidget(self.radio_bulk)
        controls_layout.addWidget(self.radio_single)
        controls_layout.addWidget(self.month_picker)
        controls_layout.addWidget(self.employee_dropdown)
        controls_layout.addStretch()
        controls_layout.addWidget(self.excel_btn)
        controls_layout.addWidget(self.pdf_btn)
        
        main_layout.addWidget(controls)
        
        # Bottom Grid
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Employee Profile", "Base Salary", "Present Days", "Deductions", "Net Salary"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("border-top-left-radius: 0px; border-top-right-radius: 0px;")
        apply_shadow(self.table)
        main_layout.addWidget(self.table)
        
        self.refresh_employees()
        
    def update_subtitle(self):
        self.subtitle.setText(f"Financial period setting: {self.month_picker.date().toString('MMMM yyyy')}")

    def toggle_mode(self):
        is_single = self.radio_single.isChecked()
        self.employee_dropdown.setVisible(is_single)

    def calculate_payslips(self):
        selected_date = self.month_picker.date()
        target_month = f"{selected_date.year()}-{selected_date.month():02d}"
        
        self.table.setRowCount(0)
        self.payslip_data.clear()
        
        is_single = self.radio_single.isChecked()
        emp_id_filter = self.employee_dropdown.currentData() if is_single else None
        
        total_liability = 0
        total_processed = 0
        
        try:
            cursor = self.db.cursor()
            if is_single and emp_id_filter:
                cursor.execute("SELECT id, name, base_salary FROM employees WHERE id = ?", (emp_id_filter,))
            else:
                cursor.execute("SELECT id, name, base_salary FROM employees")
                
            employees = cursor.fetchall()
            row_idx = 0
            for emp_id, name, base_salary in employees:
                cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = ? AND status = 'Present' AND date LIKE ?", (emp_id, f"{target_month}-%"))
                present_days = cursor.fetchone()[0]
                
                calculated_pay = round((base_salary / 30) * present_days, 2)
                deductions = round(base_salary - calculated_pay, 2)
                
                total_liability += calculated_pay
                total_processed += 1
                
                self.table.insertRow(row_idx)
                self.table.setItem(row_idx, 0, QTableWidgetItem(name))
                self.table.setItem(row_idx, 1, QTableWidgetItem(f"₹{base_salary:.2f}"))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(present_days)))
                
                deduct_item = QTableWidgetItem(f"-₹{deductions:.2f}")
                deduct_item.setForeground(QColor("#ba1a1a"))
                self.table.setItem(row_idx, 3, deduct_item)
                
                calculated_item = QTableWidgetItem(f"₹{calculated_pay:.2f}")
                calculated_item.setFont(QFont("Arial", 10, QFont.Bold))
                calculated_item.setForeground(QColor("#0058be"))
                self.table.setItem(row_idx, 4, calculated_item)
                
                self.payslip_data.append({
                    "Employee Name": name,
                    "Base Salary": base_salary,
                    "Present Days": present_days,
                    "Calculated Pay": calculated_pay
                })
                row_idx += 1
                
            self.lbl_liability.setText(f"₹{total_liability:,.2f}")
            self.lbl_paid.setText(str(total_processed))
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))

    def export_pdf(self):
        if not self.payslip_data:
            QMessageBox.warning(self, "No Data", "Please calculate payslips first.")
            return
            
        month_str = self.month_picker.date().toString('MM-yyyy')
        if self.radio_single.isChecked() and len(self.payslip_data) == 1:
            emp_name = self.payslip_data[0]['Employee Name'].replace(" ", "_")
            default_fname = f"{emp_name}.pdf"
        else:
            default_fname = f"bulk_payslip_{month_str}.pdf"
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", default_fname, "PDF Files (*.pdf)")
        if not file_path:
            return
            
        try:
            c = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter
            
            if self.radio_single.isChecked() and len(self.payslip_data) == 1:
                row = self.payslip_data[0]
                c.setFont("Helvetica-Bold", 24)
                c.drawString(50, height - 70, "A R C H I T E C T  L E D G E R")
                c.setFont("Helvetica", 12)
                c.drawString(50, height - 90, "Official Earnings Statement")
                
                c.setFont("Helvetica", 14)
                c.drawString(50, height - 130, f"Pay Period: {self.month_picker.date().toString('MMMM yyyy')}")
                
                c.rect(50, height - 300, width - 100, 150)
                c.setFont("Helvetica-Bold", 14)
                c.drawString(70, height - 180, f"Employee Name: {row['Employee Name']}")
                c.setFont("Helvetica", 14)
                c.drawString(70, height - 210, f"Base Salary Provision: ₹{row['Base Salary']:.2f}")
                c.drawString(70, height - 240, f"Present Quota: {row['Present Days']}")
                c.setFont("Helvetica-Bold", 16)
                c.drawString(70, height - 280, f"NET SALARY: ₹{row['Calculated Pay']:.2f}")
            else:
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, f"Architectural Ledger Matrix - {self.month_picker.date().toString('MM/yyyy')}")
                y = height - 100
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, "Employee Name")
                c.drawString(200, y, "Base Salary")
                c.drawString(320, y, "Present Days")
                c.drawString(450, y, "Net Payable")
                y -= 20
                c.line(50, y+10, width-50, y+10)
                
                c.setFont("Helvetica", 12)
                for row in self.payslip_data:
                    c.drawString(50, y, str(row['Employee Name']))
                    c.drawString(200, y, f"₹{row['Base Salary']:.2f}")
                    c.drawString(320, y, str(row['Present Days']))
                    c.drawString(450, y, f"₹{row['Calculated Pay']:.2f}")
                    y -= 20
                    if y < 50:
                        c.showPage()
                        y = height - 50
                        c.setFont("Helvetica", 12)
            c.save()
            QMessageBox.information(self, "Success", "PDF exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def export_excel(self):
        if not self.payslip_data:
            QMessageBox.warning(self, "No Data", "Please calculate payslips first.")
            return
            
        month_str = self.month_picker.date().toString('MM-yyyy')
        if self.radio_single.isChecked() and len(self.payslip_data) == 1:
            emp_name = self.payslip_data[0]['Employee Name'].replace(" ", "_")
            default_fname = f"{emp_name}.xlsx"
        else:
            default_fname = f"bulk_payslip_{month_str}.xlsx"
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel", default_fname, "Excel Files (*.xlsx)")
        if not file_path:
            return
            
        try:
            df = pd.DataFrame(self.payslip_data)
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Success", "Excel exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


class DashboardWindow(QMainWindow):
    def __init__(self, db_connection):
        super().__init__()
        self.db = db_connection
        self.setWindowTitle("Architect Ledger")
        self.resize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar Layer
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 24, 0, 24)
        
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(10)
        brand_layout.setContentsMargins(24, 0, 24, 24)
        
        logo_label = QLabel()
        pixmap = QPixmap("/home/abhishek/pms/image.png")
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaledToWidth(212, Qt.SmoothTransformation))
        else:
            logo_label.setText("Rishabh Tours")
            logo_label.setStyleSheet("color: white; font-weight: bold; font-size: 20px;")
            
        sub_brand = QLabel("PAYROLL ENTERPRISE")
        sub_brand.setStyleSheet("color: #94a3b8; font-family: 'Inter', sans-serif; font-size: 10px; font-weight: bold; letter-spacing: 2px; margin-bottom: 10px;")
        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(sub_brand)
        sidebar_layout.addLayout(brand_layout)
        
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        
        self.btn_overview = QPushButton(" Dashboard")
        self.btn_add_employee = QPushButton(" Employees")
        self.btn_mark_attendance = QPushButton(" Attendance")
        self.btn_payslips = QPushButton(" Payroll Ledger")
        
        for btn in [self.btn_overview, self.btn_add_employee, self.btn_mark_attendance, self.btn_payslips]:
            btn.setCheckable(True)
            self.btn_group.addButton(btn)
            sidebar_layout.addWidget(btn)
            
        sidebar_layout.addStretch()
        
        self.btn_logout = QPushButton("  Secure Logout")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(220, 38, 38, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }
        """)
        self.btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(self.btn_logout)
        
        # Content Layer encompassing TopNavBar
        content_area = QFrame()
        content_area.setObjectName("ContentArea") 
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # TopNavBar Shell
        top_nav = QFrame()
        top_nav.setObjectName("TopNav")
        top_nav.setFixedHeight(64)
        top_nav_layout = QHBoxLayout(top_nav)
        top_nav_layout.setContentsMargins(30, 0, 30, 0)
        
        # status_label = QLabel("STATUS: SECURE 🟢")
        # status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #8590a6; letter-spacing: 1px;")
        
        admin_label = QLabel("Admin Access")
        admin_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #111c2d;")
        
        # top_nav_layout.addWidget(status_label)
        top_nav_layout.addStretch()
        top_nav_layout.addWidget(admin_label)
        
        content_layout.addWidget(top_nav)
        
        # Dynamic Widget Area
        self.stacked_widget = QStackedWidget()
        
        self.view_overview = OverviewWidget(self.db)
        self.view_add_employee = AddEmployeeWidget(self.db)
        self.view_mark_attendance = MarkAttendanceWidget(self.db)
        self.view_payslips = PayslipWidget(self.db)
        
        self.stacked_widget.addWidget(self.view_overview)
        self.stacked_widget.addWidget(self.view_add_employee)
        self.stacked_widget.addWidget(self.view_mark_attendance)
        self.stacked_widget.addWidget(self.view_payslips)
        
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area)
        
        # Connect
        self.btn_overview.clicked.connect(self.show_overview)
        self.btn_add_employee.clicked.connect(self.show_add_employee)
        self.btn_mark_attendance.clicked.connect(self.show_mark_attendance)
        self.btn_payslips.clicked.connect(self.show_payslips)
        
        self.btn_overview.setChecked(True)
        self.stacked_widget.setCurrentWidget(self.view_overview)
        
    def show_overview(self):
        self.stacked_widget.setCurrentWidget(self.view_overview)

    def show_add_employee(self):
        self.view_add_employee.refresh_recent()
        self.stacked_widget.setCurrentWidget(self.view_add_employee)
        
    def show_mark_attendance(self):
        self.view_mark_attendance.refresh_grid()
        self.stacked_widget.setCurrentWidget(self.view_mark_attendance)

    def show_payslips(self):
        self.view_payslips.refresh_employees()
        self.stacked_widget.setCurrentWidget(self.view_payslips)

    def logout(self):
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dashboard = None
        self.setObjectName("LoginWindow") 
        self.setWindowTitle("Architect Ledger Access")
        self.resize(1200, 800) 
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        card = QFrame()
        card.setObjectName("CardWidget") 
        card.setStyleSheet("background-color: transparent;")
        apply_shadow(card, is_login=True)
        card.setFixedSize(900, 550)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        # Left Panel (Dark)
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #050a14; border-top-left-radius: 12px; border-bottom-left-radius: 12px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(50, 50, 50, 40)
        
        brand_lbl = QLabel()
        pixmap = QPixmap("/home/abhishek/pms/image.png")
        if not pixmap.isNull():
            brand_lbl.setPixmap(pixmap.scaledToWidth(300, Qt.SmoothTransformation))
        else:
            brand_lbl.setText("Rishabh Tours & Travels")
            brand_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 20px;")
        
        head_lbl = QLabel("<span style='color: white;'>Gandhidham's Best<br></span><span style='color: #4edea3;'>Corporate Transport.</span>")
        head_lbl.setTextFormat(Qt.RichText)
        head_lbl.setStyleSheet("font-weight: 800; font-family: 'Manrope', sans-serif; font-size: 34px; margin-top: 20px;")
        head_lbl.setWordWrap(True)
        
        # sub_lbl = QLabel("We have a long list of satisfied corporate and retail clients across Gujarat. Our drivers are well-trained and hospitable, with a 24x7 employee helpline. Known for quality service, competitive pricing, and industry-leading repeat rates.")
        # sub_lbl.setStyleSheet("color: #bcc7de; font-size: 15px; margin-top: 20px; line-height: 1.5;")
        # sub_lbl.setWordWrap(True)
        
        left_layout.addWidget(brand_lbl)
        left_layout.addWidget(head_lbl)
        # left_layout.addWidget(sub_lbl)
        left_layout.addStretch()
        
        # db_status = QFrame()
        # db_status.setStyleSheet("background-color: rgba(255,255,255,0.1); border-radius: 8px; padding: 15px;")
        # db_layout = QVBoxLayout(db_status)
        # db_layout.setContentsMargins(0,0,0,0)
        # db_layout.setSpacing(4)
        # db_title = QLabel("DATABASE STATUS")
        # db_title.setStyleSheet("color: #8590a6; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        # db_val = QLabel("SQLCipher AES-256 Active")
        # db_val.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        # db_layout.addWidget(db_title)
        # db_layout.addWidget(db_val)
        # left_layout.addWidget(db_status)
        
        # Right Panel (Light)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #ffffff; border-top-right-radius: 12px; border-bottom-right-radius: 12px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 60, 40, 40)
        right_layout.setSpacing(15)
        
        title = QLabel("System Admin Access")
        title.setProperty("class", "TitleLabel")
        
        sub = QLabel("Enter Admin Credentials to proceed to the main ledger.")
        sub.setProperty("class", "SubtitleLabel")
        sub.setStyleSheet("margin-bottom: 20px;")
        sub.setWordWrap(True)
        
        right_layout.addWidget(title)
        right_layout.addWidget(sub)
        
        pwd_label = QLabel("MASTER PASSWORD")
        pwd_label.setStyleSheet("color: #45474c; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        right_layout.addWidget(pwd_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("••••••••••••")
        self.password_input.setStyleSheet("background-color: #e7eeff; border-radius: 8px; padding: 15px; font-size: 18px; color: #091426;")
        right_layout.addWidget(self.password_input)
        
        enc_label = QLabel("Encryption: AES-256 Multi-Layered Shell")
        enc_label.setStyleSheet("color: #8590a6; font-size: 10px; font-style: italic;")
        right_layout.addWidget(enc_label)
        
        options_layout = QHBoxLayout()
        rem_checkbox = QCheckBox("Remember Station")
        rem_checkbox.setStyleSheet("color: #111c2d; font-size: 12px; font-weight: 500;")
        reset_lbl = QLabel("Reset Key")
        reset_lbl.setStyleSheet("color: #0058be; font-size: 12px; font-weight: bold;")
        options_layout.addWidget(rem_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(reset_lbl)
        right_layout.addLayout(options_layout)
        
        right_layout.addSpacing(15)
        
        self.login_btn = QPushButton("Login →")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0058be;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2170e4;
            }
        """)
        self.login_btn.setMinimumHeight(48)
        self.login_btn.clicked.connect(self.attempt_login)
        right_layout.addWidget(self.login_btn)
        
        right_layout.addStretch()
        
        # sys_status = QLabel("<span style='color: #4edea3;'>●</span> SYSTEM STATUS: SECURE")
        # sys_status.setStyleSheet("color: #8590a6; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        # right_layout.addWidget(sys_status)
        
        card_layout.addWidget(left_panel, stretch=9)
        card_layout.addWidget(right_panel, stretch=11)
        
        main_layout.addWidget(card)

    def attempt_login(self):
        pwd = self.password_input.text()
        db_conn = verify_and_unlock(pwd)
        
        if db_conn:
            self.dashboard = DashboardWindow(db_conn)
            self.dashboard.showMaximized()
            self.close() 
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect password or corrupted database.")
            self.password_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(MAIN_STYLE)
    
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
