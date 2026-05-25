def nhap_bai_toan_goc():
    print("--- CHƯƠNG TRÌNH NHẬP BÀI TOÁN QUY HOẠCH TUYẾN TÍNH (GỐC) ---")
    
    # 1. Nhập thông tin kích thước
    num_vars = int(input("Nhập số lượng biến gốc (n): "))
    num_constraints = int(input("Nhập số lượng ràng buộc (m): "))
    opt_type = input("Hàm mục tiêu là Max hay Min? ").strip().capitalize()

    # 1.5 Nhập điều kiện của biến
    print("\n--- Nhập điều kiện của các biến ---")
    print("Gợi ý: Nhập '>=', '<=', hoặc 'free' (tự do). Nhấn Enter để dùng mặc định '>='.")
    x_conditions = []
    for i in range(1, num_vars + 1):
        cond = input(f"  Điều kiện của x{i} [>=]: ").strip().lower()
        if cond in ['<=', '<=0', '<= 0']:
            x_conditions.append('<= 0')
        elif cond in ['free', 'tu do', 'tự do']:
            x_conditions.append('tự do')
        else:
            x_conditions.append('>= 0') # Mặc định nếu nhập sai hoặc bỏ trống

    # 2. Nhập hệ số hàm mục tiêu (giữ nguyên không đổi dấu)
    print("\n--- Nhập hệ số hàm mục tiêu ---")
    c = []
    for i in range(1, num_vars + 1):
        val = float(input(f"  Hệ số của x{i}: "))
        c.append(val)

    # 3. Nhập các ràng buộc (Lưu nguyên trạng)
    print("\n--- Nhập các ràng buộc ---")
    constraints = []
    
    for i in range(1, num_constraints + 1):
        print(f"Ràng buộc {i}:")
        row = []
        for j in range(1, num_vars + 1):
            row.append(float(input(f"  Hệ số x{j}: ")))
        
        sign = input("  Dấu (<=, >=, =): ").strip()
        rhs = float(input("  Vế phải (b): "))
        
        # Lưu vào một dictionary để giữ nguyên cấu trúc gốc
        constraints.append({
            "A_row": row,
            "sign": sign,
            "b": rhs
        })

    # 4. In lại bài toán vừa nhập để xác nhận
    print("\n==================================================")
    print("XÁC NHẬN BÀI TOÁN GỐC ĐÃ NHẬP:")
    print("--------------------------------------------------")
    
    # In hàm mục tiêu
    obj_terms = []
    for i in range(num_vars):
        coeff = c[i]
        if coeff != 0:
            obj_terms.append(f"{coeff}*x{i+1}")
    obj_str = " + ".join(obj_terms).replace("+ -", "- ")
    print(f"{opt_type} Z = {obj_str if obj_str else '0'}")
    
    # In ràng buộc
    print("Thỏa mãn các ràng buộc:")
    for idx, const in enumerate(constraints):
        row = const["A_row"]
        row_terms = []
        for i in range(num_vars):
            coeff = row[i]
            if coeff != 0:
                row_terms.append(f"{coeff}*x{i+1}")
                
        row_str = " + ".join(row_terms).replace("+ -", "- ")
        # Xử lý trường hợp dòng toàn số 0
        if not row_str: 
            row_str = "0"
            
        print(f"  ({idx+1})  {row_str} {const['sign']} {const['b']}")
        
    # In điều kiện của từng biến
    print("Điều kiện của các biến:")
    for i in range(num_vars):
        print(f"  x{i+1} {x_conditions[i]}")
    print("==================================================\n")
    
    # Trả về dữ liệu thô kèm theo mảng x_conditions
    return opt_type, c, constraints, x_conditions


