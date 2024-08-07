document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("transfer_location_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/transfer_location', formData)
        .then(function(response) {
            swal.fire({
                text: response.data,
                icon: "info",
                confirmButtonText: "확인"
            });
        })
        .catch(function(error) {
            console.error('Error:', error);
            let errorMessage = "오류가 발생했습니다.";
            if (error.response && error.response.data) {
                errorMessage = error.response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
            }
            swal.fire({
                title: "오류",
                html: errorMessage,
                icon: "error",
                confirmButtonText: "확인"
            });
        });      
    });
});