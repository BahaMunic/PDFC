import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, END, ANCHOR
import fitz  # PyMuPDF
from PIL import Image
import os
import threading

# --- إعدادات جودة الضغط لـ PDF ---
PDF_COMPRESSION_SETTINGS = {
    "خفيف": {"dpi": 200, "quality": 90},
    "وسط":  {"dpi": 150, "quality": 80},
    "عالي": {"dpi": 75,  "quality": 70}
}

class FileToolkitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- إعدادات النافذة الرئيسية ---
        self.title("مجموعة أدوات معالجة الملفات")
        self.geometry("700x550")
        self.resizable(True, True)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- إنشاء واجهة التبويبات ---
        self.tab_view = ctk.CTkTabview(self, width=680)
        self.tab_view.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_view.add("ضغط PDF")
        self.tab_view.add("دمج PDF")
        self.tab_view.add("صور إلى PDF")
        self.tab_view.add("ضغط الصور")

        self.tab_view.set("ضغط PDF") # التبويب الافتراضي

        # --- إنشاء محتوى كل تبويب ---
        self.create_pdf_compressor_tab()
        self.create_pdf_merger_tab()
        self.create_images_to_pdf_tab()
        self.create_image_compressor_tab()

    def run_in_thread(self, target_func, *args):
        """دالة مساعدة لتشغيل أي وظيفة في خيط منفصل لتجنب تجميد الواجهة"""
        thread = threading.Thread(target=target_func, args=args, daemon=True)
        thread.start()

    # =================================================================================
    # --- التبويب الأول: ضغط PDF ---
    # =================================================================================
    def create_pdf_compressor_tab(self):
        tab = self.tab_view.tab("ضغط PDF")

        # متغيرات خاصة بهذا التبويب
        self.pdf_compress_path = ctk.StringVar()

        ctk.CTkLabel(tab, text="أداة لتقليل حجم ملفات PDF", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        # --- اختيار الملف ---
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkButton(file_frame, text="اختر ملف PDF", command=self.browse_pdf_compress).pack(side="left", padx=10)
        ctk.CTkEntry(file_frame, textvariable=self.pdf_compress_path, state="readonly").pack(side="left", fill="x", expand=True, padx=10)

        # --- اختيار مستوى الضغط ---
        ctk.CTkLabel(tab, text="اختر مستوى الضغط:", font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        self.pdf_compress_level = ctk.StringVar(value="وسط")
        ctk.CTkSegmentedButton(tab, values=list(PDF_COMPRESSION_SETTINGS.keys()), variable=self.pdf_compress_level).pack(pady=5, padx=20, fill="x")

        # --- زر البدء والتقدم ---
        self.pdf_compress_button = ctk.CTkButton(tab, text="ابدأ الضغط", command=lambda: self.run_in_thread(self.compress_pdf))
        self.pdf_compress_button.pack(pady=20, ipady=10)
        self.pdf_compress_status = ctk.CTkLabel(tab, text="جاهز للبدء")
        self.pdf_compress_status.pack(pady=5)

    def browse_pdf_compress(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_compress_path.set(path)

    def compress_pdf(self):
        input_path = self.pdf_compress_path.get()
        if not input_path:
            messagebox.showerror("خطأ", "الرجاء اختيار ملف PDF أولاً.")
            return

        level = self.pdf_compress_level.get()
        settings = PDF_COMPRESSION_SETTINGS[level]
        output_path = f"{os.path.splitext(input_path)[0]}_مضغوط_{level}.pdf"

        try:
            self.pdf_compress_status.configure(text="جاري المعالجة...")
            doc = fitz.open(input_path)
            images = []
            for i, page in enumerate(doc):
                self.pdf_compress_status.configure(text=f"معالجة صفحة {i+1}/{len(doc)}")
                pix = page.get_pixmap(dpi=settings["dpi"])
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)

            if images:
                images[0].save(output_path, "PDF", resolution=100.0, save_all=True, append_images=images[1:], quality=settings["quality"])

            self.pdf_compress_status.configure(text="اكتملت العملية بنجاح!")
            messagebox.showinfo("نجاح", f"تم ضغط الملف وحفظه في:\n{output_path}")
        except Exception as e:
            self.pdf_compress_status.configure(text="حدث خطأ!")
            messagebox.showerror("خطأ", f"فشلت العملية: {e}")
        finally:
            self.pdf_compress_status.configure(text="جاهز لعملية جديدة.")

    # =================================================================================
    # --- التبويب الثاني: دمج PDF ---
    # =================================================================================
    def create_pdf_merger_tab(self):
        tab = self.tab_view.tab("دمج PDF")
        ctk.CTkLabel(tab, text="أداة لدمج عدة ملفات PDF في ملف واحد", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.pdf_merge_listbox = Listbox(list_frame, selectmode="extended", bg="#2B2B2B", fg="white", borderwidth=0, highlightthickness=0)
        self.pdf_merge_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=5)

        ctk.CTkButton(btn_frame, text="إضافة ملفات", command=self.add_pdfs_to_merge).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="إزالة المحدد", command=lambda: self.remove_from_listbox(self.pdf_merge_listbox)).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="▲ تحريك لأعلى", command=lambda: self.move_item_in_listbox(self.pdf_merge_listbox, -1)).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="▼ تحريك لأسفل", command=lambda: self.move_item_in_listbox(self.pdf_merge_listbox, 1)).pack(pady=5, fill="x")

        self.pdf_merge_button = ctk.CTkButton(tab, text="ابدأ الدمج", command=lambda: self.run_in_thread(self.merge_pdfs))
        self.pdf_merge_button.pack(pady=20, ipady=10)

    def add_pdfs_to_merge(self):
        paths = filedialog.askopenfilenames(title="اختر ملفات PDF للدمج", filetypes=[("PDF Files", "*.pdf")])
        for path in paths:
            self.pdf_merge_listbox.insert(END, path)

    def merge_pdfs(self):
        files = self.pdf_merge_listbox.get(0, END)
        if len(files) < 2:
            messagebox.showwarning("تنبيه", "الرجاء اختيار ملفين على الأقل للدمج.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="حفظ الملف المدمج كـ")
        if not output_path:
            return

        try:
            merged_doc = fitz.open()
            for file_path in files:
                with fitz.open(file_path) as doc_to_merge:
                    merged_doc.insert_pdf(doc_to_merge)

            merged_doc.save(output_path, garbage=4, deflate=True)
            merged_doc.close()
            messagebox.showinfo("نجاح", f"تم دمج الملفات بنجاح في:\n{output_path}")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشلت عملية الدمج: {e}")

    # =================================================================================
    # --- التبويب الثالث: صور إلى PDF ---
    # =================================================================================
    def create_images_to_pdf_tab(self):
        tab = self.tab_view.tab("صور إلى PDF")
        ctk.CTkLabel(tab, text="أداة لتحويل مجموعة صور إلى ملف PDF واحد", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        list_frame = ctk.CTkFrame(tab)
        list_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.img_to_pdf_listbox = Listbox(list_frame, selectmode="extended", bg="#2B2B2B", fg="white", borderwidth=0, highlightthickness=0)
        self.img_to_pdf_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.pack(side="right", fill="y", padx=5)

        ctk.CTkButton(btn_frame, text="إضافة صور", command=self.add_images_to_convert).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="إزالة المحدد", command=lambda: self.remove_from_listbox(self.img_to_pdf_listbox)).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="▲ تحريك لأعلى", command=lambda: self.move_item_in_listbox(self.img_to_pdf_listbox, -1)).pack(pady=5, fill="x")
        ctk.CTkButton(btn_frame, text="▼ تحريك لأسفل", command=lambda: self.move_item_in_listbox(self.img_to_pdf_listbox, 1)).pack(pady=5, fill="x")

        self.img_to_pdf_button = ctk.CTkButton(tab, text="ابدأ التحويل إلى PDF", command=lambda: self.run_in_thread(self.convert_images_to_pdf))
        self.img_to_pdf_button.pack(pady=20, ipady=10)

    def add_images_to_convert(self):
        paths = filedialog.askopenfilenames(title="اختر الصور", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        for path in paths:
            self.img_to_pdf_listbox.insert(END, path)

    def convert_images_to_pdf(self):
        image_paths = self.img_to_pdf_listbox.get(0, END)
        if not image_paths:
            messagebox.showwarning("تنبيه", "الرجاء اختيار صورة واحدة على الأقل.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")], title="حفظ ملف PDF الناتج كـ")
        if not output_path:
            return

        try:
            images_to_save = [Image.open(p).convert("RGB") for p in image_paths]

            if images_to_save:
                images_to_save[0].save(output_path, save_all=True, append_images=images_to_save[1:])

            messagebox.showinfo("نجاح", f"تم تحويل الصور إلى PDF بنجاح في:\n{output_path}")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشلت عملية التحويل: {e}")

    # =================================================================================
    # --- التبويب الرابع: ضغط الصور ---
    # =================================================================================
    def create_image_compressor_tab(self):
        tab = self.tab_view.tab("ضغط الصور")
        ctk.CTkLabel(tab, text="أداة لتقليل حجم الصور", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        ctk.CTkButton(tab, text="اختر صوراً للضغط", command=self.select_images_to_compress).pack(pady=10)

        self.img_compress_listbox = Listbox(tab, selectmode="extended", bg="#2B2B2B", fg="white", borderwidth=0, highlightthickness=0, height=8)
        self.img_compress_listbox.pack(pady=5, padx=20, fill="x")

        quality_frame = ctk.CTkFrame(tab)
        quality_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(quality_frame, text="جودة الضغط (1-100):").pack(side="left", padx=10)
        self.img_quality_slider = ctk.CTkSlider(quality_frame, from_=1, to=100, number_of_steps=99)
        self.img_quality_slider.set(85)
        self.img_quality_slider.pack(side="left", fill="x", expand=True)

        self.img_compress_button = ctk.CTkButton(tab, text="ابدأ ضغط الصور", command=lambda: self.run_in_thread(self.compress_images))
        self.img_compress_button.pack(pady=20, ipady=10)
        self.img_compress_status = ctk.CTkLabel(tab, text="جاهز للبدء")
        self.img_compress_status.pack(pady=5)

    def select_images_to_compress(self):
        paths = filedialog.askopenfilenames(title="اختر الصور", filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        self.img_compress_listbox.delete(0, END)
        for path in paths:
            self.img_compress_listbox.insert(END, path)

    def compress_images(self):
        image_paths = self.img_compress_listbox.get(0, END)
        if not image_paths:
            messagebox.showwarning("تنبيه", "الرجاء اختيار صورة واحدة على الأقل.")
            return

        quality = int(self.img_quality_slider.get())

        try:
            # إنشاء مجلد فرعي لحفظ الصور المضغوطة
            output_dir = os.path.join(os.path.dirname(image_paths[0]), "صور مضغوطة")
            os.makedirs(output_dir, exist_ok=True)

            for i, img_path in enumerate(image_paths):
                self.img_compress_status.configure(text=f"ضغط صورة {i+1}/{len(image_paths)}")
                img = Image.open(img_path).convert("RGB") # تحويل لـ RGB لضمان التوافق مع JPEG

                filename = os.path.basename(img_path)
                name, _ = os.path.splitext(filename)
                output_path = os.path.join(output_dir, f"{name}_مضغوط.jpg")

                img.save(output_path, "JPEG", quality=quality, optimize=True)

            messagebox.showinfo("نجاح", f"تم ضغط جميع الصور وحفظها في المجلد:\n{output_dir}")
            self.img_compress_status.configure(text="اكتملت العملية بنجاح!")
        except Exception as e:
            self.img_compress_status.configure(text="حدث خطأ!")
            messagebox.showerror("خطأ", f"فشلت عملية الضغط: {e}")

    # =================================================================================
    # --- دوال مساعدة للـ Listbox ---
    # =================================================================================
    def remove_from_listbox(self, listbox):
        selected_indices = listbox.curselection()
        # الحذف من الأسفل للأعلى لتجنب مشاكل تغيير الفهرس
        for i in sorted(selected_indices, reverse=True):
            listbox.delete(i)

    def move_item_in_listbox(self, listbox, direction):
        selected_indices = listbox.curselection()
        if not selected_indices:
            return

        for i in selected_indices:
            if 0 <= i + direction < listbox.size():
                item = listbox.get(i)
                listbox.delete(i)
                listbox.insert(i + direction, item)
                listbox.selection_set(i + direction)

if __name__ == "__main__":
    app = FileToolkitApp()
    app.mainloop()
