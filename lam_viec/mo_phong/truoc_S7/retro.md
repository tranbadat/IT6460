# Ghi chép họp cải tiến cuối sprint

Mỗi sprint một mục. Ghi ngắn: điều làm tốt, điều cần cải thiện, hành động. Mỗi ý bắt đầu bằng mã để báo cáo bài học trích dẫn được.

## S1
- R-S1-01 (tốt): Khung ứng dụng giao diện tái sử dụng thư viện từ hợp đồng tương tự, gói 4.3.3 hoàn thành trước kế hoạch. Liên kết: 4.3.3, RR20.
- R-S1-02 (cần cải thiện): Danh sách đối tượng phỏng vấn người dùng chưa được thống nhất với Chủ sản phẩm tại họp khởi động, phải bổ sung giữa sprint. Liên kết: 2.2.3, VD01.
- R-S1-03 (hành động): Gửi Chủ đầu tư danh sách tài liệu Main System cần cung cấp trước hạn cam kết CK1 ngày 14/04/2027. Liên kết: 4.2.5, RR02.

## S2
- R-S2-01 (tốt): Mốc M1 đạt đúng hạn, kế hoạch quản lý dự án được Chủ đầu tư xác nhận trong thời gian phê duyệt. Liên kết: M1, 3.1.2.
- R-S2-02 (cần cải thiện): Ngày có mặt của vị trí bổ sung chưa được xác nhận lại trước sprint huy động, kỹ sư kiểm thử có mặt muộn 2 ngày. Liên kết: RR04, VD03.
- R-S2-03 (hành động): Xác nhận ngày có mặt của Phạm Ngọc Anh và Trương Quốc Việt trước sprint S3 một tuần, theo dõi phản hồi của Chủ đầu tư về tài liệu Main System hằng ngày. Liên kết: RR04, RR02, S3.

## S3
- R-S3-01 (tốt): Đặc tả yêu cầu và giao diện ưu tiên được xác nhận đúng kế hoạch, mốc M2 đạt trước hạn. Liên kết: M2, 3.2.5.
- R-S3-02 (cần cải thiện): Tài liệu Main System đến muộn làm gói găng 4.2.7 bắt đầu muộn, nhóm chưa chuẩn bị sẵn phần đặc tả giao diện có thể làm trước khi có tài liệu. Liên kết: RR02, 4.2.5, VD06.
- R-S3-03 (hành động): Đề nghị Chủ đầu tư xác nhận sớm lịch bàn giao môi trường thử Main System (CK2) và thay đổi phía Main System (CK8), theo dõi hằng tuần trong họp tiến độ. Liên kết: RR02, 4.4.3.
- R-S3-04 (cần cải thiện): Lỗi tạo trùng đơn hàng mức cao cho thấy cần bổ sung kịch bản gửi lặp vào bộ kiểm thử đơn vị của các dịch vụ ghi dữ liệu. Liên kết: 3.3.5, 3.4.1.

## S4
- R-S4-01 (tốt): Dùng quỹ sẵn sàng của các vị trí phía máy chủ để làm bù các gói chậm, dịch vụ giả lập Main System dùng lại công cụ có sẵn nên chuỗi găng được rút ngắn. Liên kết: 4.4.1, VD07.
- R-S4-02 (cần cải thiện): Ước lượng dịch vụ đổi trả chưa tính trường hợp hoàn tiền một phần đã nêu trong đặc tả, cần rà soát các trường hợp ngoại lệ của đặc tả trước khi lập trình. Liên kết: 3.3.7, 3.2.11.
- R-S4-03 (hành động): Đánh giá tác động của yêu cầu bán hàng trên sàn thương mại điện tử trong thời hạn đánh giá và trình ban kiểm soát thay đổi. Liên kết: CR01, VD08.

## S5
- R-S5-01 (tốt): Yêu cầu thay đổi CR01 được đánh giá và trình phụ lục trong 5 ngày làm việc, lịch lập lại giữ dự trữ đến cut over. Liên kết: CR01, VD08.
- R-S5-02 (cần cải thiện): Lỗi giữ tồn kho khi thanh toán thất bại chỉ phát hiện ở kiểm thử đầu cuối, kiểm thử đơn vị dịch vụ giỏ hàng chưa phủ nhánh thất bại. Liên kết: 3.4.6, 3.3.1.
- R-S5-03 (hành động): Bổ sung ca kiểm thử nhánh thanh toán thất bại vào bộ kiểm thử tự động trước kiểm thử hệ thống. Liên kết: 3.4.10, RR03.

## S6
- R-S6-01 (tốt): Kiểm thử tích hợp với Main System đạt, rủi ro tài liệu và môi trường Main System được đóng. Liên kết: RR02, 4.4.3, 4.4.4.
- R-S6-02 (cần cải thiện): Giới hạn tần suất gọi của sàn chỉ được biết khi thiết kế tích hợp, khảo sát 5.2.1 chưa kiểm tra đủ điều kiện kỹ thuật của giao diện lập trình. Liên kết: 5.2.1, 5.2.3, RR22.
- R-S6-03 (hành động): Lập danh sách điều kiện kỹ thuật của sàn (giới hạn tần suất, thời hạn khóa, môi trường thử) và đối chiếu trước khi lập trình 5.3. Liên kết: RR22, 5.3.1.
