// File: static/js/SearchBar.js

const { useState, useEffect, useCallback } = React;

function SearchBar(props) {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);

    // Hàm gọi API để lấy gợi ý, sử dụng useCallback để tối ưu
    const fetchSuggestions = useCallback(async (searchQuery) => {
        if (searchQuery.length > 1) {
            try {
                const response = await fetch(`${props.suggestionsUrl}?q=${encodeURIComponent(searchQuery)}`);
                const data = await response.json();
                setSuggestions(data);
            } catch (error) {
                console.error("Lỗi khi lấy gợi ý:", error);
                setSuggestions([]);
            }
        } else {
            setSuggestions([]);
        }
    }, [props.suggestionsUrl]);

    // Sử dụng useEffect để theo dõi sự thay đổi của query và gọi API sau một khoảng trễ
    useEffect(() => {
        const debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
        }, 300); // Chờ 300ms sau khi người dùng ngừng gõ

        return () => clearTimeout(debounceTimer);
    }, [query, fetchSuggestions]);

    // Hàm xử lý khi nhấn nút tìm kiếm hoặc Enter
    const handleSearch = () => {
        if (query.trim()) {
            window.location.href = `${props.searchUrl}?q=${encodeURIComponent(query.trim())}`;
        }
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="search-bar-container shadow">
            <div className="input-group">
                <span className="input-group-text bg-transparent border-0 pe-1">
                    <i className="fas fa-search text-muted"></i>
                </span>
                <input
                    type="text"
                    className="form-control border-0"
                    placeholder="Tìm kiếm bác sĩ, bệnh viện..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                />
                <button className="btn btn-primary rounded-end" type="button" onClick={handleSearch}>
                    Tìm kiếm
                </button>
            </div>
            {suggestions.length > 0 && (
                <div className="list-group position-absolute w-100 mt-1 shadow-sm" style={{ zIndex: 1031 }}>
                    {suggestions.map((suggestion, index) => (
                        <a key={index} href={`${props.searchUrl}?q=${encodeURIComponent(suggestion.split(' - ')[0].trim())}`} className="list-group-item list-group-item-action">
                            {suggestion}
                        </a>
                    ))}
                </div>
            )}
        </div>
    );
}