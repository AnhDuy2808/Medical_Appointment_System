// File: static/js/DoctorList.js

const { useState, useEffect } = React;

function DoctorList({ apiUrl, detailsUrl, bookingUrl }) {
    const [doctors, setDoctors] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchDoctors() {
            try {
                const response = await fetch(apiUrl);
                const data = await response.json();
                setDoctors(data);
            } catch (error) {
                console.error("Lỗi khi tải danh sách bác sĩ:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchDoctors();
    }, [apiUrl]);

    if (loading) {
        return <p className="text-center">Đang tải danh sách bác sĩ...</p>;
    }

    if (doctors.length === 0) {
        return <p className="text-center">Không có bác sĩ nào để hiển thị.</p>;
    }

    return (
        <div className="row">
            {doctors.map(doctor => (
                <div key={doctor.id} className="col-md-4 mb-4">
                    <a href={`${detailsUrl}/${doctor.id}`} className="card-link">
                        <div className="card h-100 shadow-sm border-0 card-hover">
                            <div className="text-center pt-3">
                                <img src={doctor.avatar || '/static/images/default_avatar.jpg'} className="rounded-circle" alt={doctor.full_name} style={{ width: '150px', height: '150px', objectFit: 'cover' }} />
                            </div>
                            <div className="card-body text-center d-flex flex-column">
                                <h5 className="card-title mt-2">{doctor.full_name}</h5>
                                {doctor.experience_years && (
                                    <p className="card-text text-muted small">
                                        <i className="fas fa-medal fa-fw me-1"></i>
                                        <strong>{doctor.experience_years}</strong> năm kinh nghiệm
                                    </p>
                                )}
                                <p className="card-text text-muted small">
                                    <i className="fas fa-stethoscope fa-fw me-1"></i>
                                    {doctor.specialty || 'Chuyên khoa chưa cập nhật'}
                                </p>
                                <p className="card-text text-muted small">
                                    <i className="fas fa-hospital fa-fw me-1"></i>
                                    {doctor.medical_center || 'Nơi công tác chưa cập nhật'}
                                </p>
                                <div className="mt-auto pt-2">
                                    <span className="btn btn-primary btn-sm">Xem chi tiết</span>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
            ))}
        </div>
    );
}