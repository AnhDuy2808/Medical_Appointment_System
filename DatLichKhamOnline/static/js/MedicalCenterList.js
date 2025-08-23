// File: static/js/MedicalCenterList.js

function MedicalCenterList({ apiUrl, detailsUrl }) {
    const [centers, setCenters] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchCenters() {
            try {
                const response = await fetch(apiUrl);
                const data = await response.json();
                setCenters(data);
            } catch (error) {
                console.error("Lỗi khi tải danh sách trung tâm y tế:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchCenters();
    }, [apiUrl]);

    if (loading) {
        return <p className="text-center">Đang tải danh sách trung tâm y tế...</p>;
    }

    if (centers.length === 0) {
        return <p className="text-center">Không có trung tâm y tế nào để hiển thị.</p>;
    }

    return (
        <div className="row">
            {centers.map(center => (
                <div key={center.id} className="col-md-4 mb-4">
                    <a href={`${detailsUrl}/${center.id}`} className="card-link">
                        <div className="card h-100 shadow-sm border-0 card-hover">
                            <img src={center.image || '/static/images/default_hospital.jpg'} className="card-img-top" alt={center.name} style={{ height: '200px', objectFit: 'cover' }} />
                            <div className="card-body">
                                <h5 className="card-title">
                                    <i className="fas fa-hospital-alt me-2 text-primary"></i>{center.name}
                                </h5>
                                <p className="card-text text-muted">{center.description}</p>
                            </div>
                        </div>
                    </a>
                </div>
            ))}
        </div>
    );
}