# 📚 Documentation Index

## 🎯 Chọn tài liệu phù hợp với bạn

### ⚠️ Gặp lỗi Python 3.13?
👉 **[PYTHON_FIX.md](PYTHON_FIX.md)** hoặc chạy `./fix_python.sh`
- 🔧 Lỗi: AttributeError khi pip install
- 🔧 Fix tự động trong 5 phút
- 🔧 Script ready-to-use

### 1️⃣ Bạn muốn biết: "Code chạy trên OS gì?"
👉 **[PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)**
- ✅ Kali Linux có chạy được không?
- ✅ Windows có chạy được không?  
- ✅ So sánh performance giữa các OS
- ✅ Code có cần sửa không?

### 2️⃣ Bạn muốn: "Chạy nhanh nhất có thể"
👉 **[QUICK_START.md](QUICK_START.md)**
- ⚡ Commands chạy theo từng platform
- ⚡ TL;DR - Không cần đọc nhiều
- ⚡ FAQs nhanh
- ⚡ Common mistakes

### 3️⃣ Bạn cần: "Hướng dẫn chi tiết từng bước"
👉 **[PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)**
- 📖 Hướng dẫn đầy đủ cho Kali Linux
- 📖 Hướng dẫn đầy đủ cho Ubuntu
- 📖 Hướng dẫn đầy đủ cho Windows + WSL2
- 📖 Troubleshooting chi tiết

### 4️⃣ Bạn muốn: "Cấu hình và tối ưu hóa"
👉 **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**
- 🔧 Cấu hình chi tiết
- 🔧 Training AI models
- 🔧 Testing scenarios
- 🔧 Performance tuning
- 🔧 Production deployment

### 5️⃣ Bạn muốn: "Tổng quan dự án"
👉 **[README.md](README.md)**
- 📋 Giới thiệu dự án
- 📋 Kiến trúc hệ thống
- 📋 Features chính
- 📋 Quick start links

---

## 🗺️ Workflow Khuyến nghị

### Lần đầu tiên:

```
1. Đọc README.md (5 phút)
   ↓
2. Kiểm tra PLATFORM_COMPATIBILITY.md (2 phút) 
   ↓
3. Follow QUICK_START.md cho OS của bạn (10 phút)
   ↓
4. Chạy thử hệ thống
   ↓
5. Nếu cần chi tiết hơn → DEPLOYMENT_GUIDE.md
```

### Khi gặp vấn đề:

```
1. Chạy ./check_system.sh
   ↓
2. Xem phần Troubleshooting trong PLATFORM_GUIDE.md
   ↓
3. Check FAQs trong QUICK_START.md
```

---

## 📖 Chi tiết từng File

### [README.md](README.md)
**Mục đích**: Overview và entry point  
**Nội dung**:
- Giới thiệu dự án
- Kiến trúc tổng thể
- Quick start links
- Features list

**Đọc khi**: Lần đầu tiên tìm hiểu dự án

---

### [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)
**Mục đích**: Trả lời câu hỏi "Chạy được trên OS nào?"  
**Nội dung**:
- Support matrix cho tất cả OS
- Performance comparison
- Kali Linux compatibility ⭐
- Windows compatibility
- FAQs về platform

**Đọc khi**: 
- Muốn biết OS của bạn có chạy được không
- Băn khoăn giữa nhiều OS

---

### [QUICK_START.md](QUICK_START.md)  
**Mục đích**: Chạy nhanh nhất có thể  
**Nội dung**:
- TL;DR commands cho mỗi OS
- No explanation, just do it!
- Common mistakes
- Quick FAQs

**Đọc khi**:
- Đã biết cơ bản, chỉ cần commands
- Muốn test nhanh
- Không có thời gian đọc nhiều

---

### [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
**Mục đích**: Hướng dẫn chi tiết theo platform  
**Nội dung**:
- **Kali Linux**: Full guide với commands
- **Ubuntu**: Full guide với commands  
- **Windows WSL2**: Từ cài WSL đến chạy code
- **Docker**: Alternative approach
- Troubleshooting chi tiết
- Performance tips

**Đọc khi**:
- Lần đầu cài đặt
- Gặp lỗi cần debug
- Muốn hiểu rõ từng bước

---

### [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
**Mục đích**: Production deployment và advanced config  
**Nội dung**:
- Cài đặt dependencies chi tiết
- Training AI models
- Configuration tuning
- Testing scenarios
- QoS setup
- Performance benchmarking
- Production deployment

**Đọc khi**:
- Đã chạy được cơ bản
- Muốn train custom models
- Deploy lên production
- Tối ưu performance

---

## 🎓 Learning Path

### Beginner (Mới bắt đầu):
```
1. README.md (overview)
2. PLATFORM_COMPATIBILITY.md (check OS)
3. QUICK_START.md (run it!)
```

### Intermediate (Đã chạy được):
```
1. PLATFORM_GUIDE.md (understand details)
2. DEPLOYMENT_GUIDE.md (sections 1-5)
3. Experiment với code
```

### Advanced (Muốn customize):
```
1. DEPLOYMENT_GUIDE.md (full read)
2. Study source code
3. Train custom models
4. Performance tuning
```

---

## 🔍 Quick Reference

| Câu hỏi | File cần đọc | Phần nào |
|---------|--------------|----------|
| Kali Linux chạy được không? | PLATFORM_COMPATIBILITY.md | Platform Support Matrix |
| Windows chạy như thế nào? | PLATFORM_GUIDE.md | Section: Windows với WSL2 |
| Commands để chạy nhanh? | QUICK_START.md | TL;DR section |
| Cài Mininet như thế nào? | PLATFORM_GUIDE.md | Installation section |
| Train AI model? | DEPLOYMENT_GUIDE.md | Section 3 |
| Test scenarios? | DEPLOYMENT_GUIDE.md | Section 5 |
| Lỗi OVS không start? | PLATFORM_GUIDE.md | Troubleshooting |
| Performance optimization? | DEPLOYMENT_GUIDE.md | Section 8 |

---

## 📞 Still Need Help?

1. ✅ Đã đọc đúng document chưa? (check table trên)
2. ✅ Đã chạy `./check_system.sh` chưa?
3. ✅ Đã xem Troubleshooting chưa?
4. ✅ Đã check FAQs chưa?

Nếu vẫn stuck:
- Check error logs: `logs/controller.log`
- Run verbose: `./start.sh --verbose`
- Test components riêng lẻ

---

## 🎯 Mục tiêu của từng Document

| Document | Goal | Time to read |
|----------|------|--------------|
| README | Understand what this is | 5 min |
| PLATFORM_COMPATIBILITY | Know if you can run it | 2 min |
| QUICK_START | Get it running ASAP | 5 min |
| PLATFORM_GUIDE | Understand how to run on your OS | 15 min |
| DEPLOYMENT_GUIDE | Master the system | 30+ min |

---

**🎉 Happy Learning!**

> 💡 **Pro tip**: Start với QUICK_START.md, chỉ đọc detail khi cần!
