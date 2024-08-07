document.getElementById("view_police_investigation_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("view_police_investigation").style.display = "block";
});

document.getElementById("enroll_evidence_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("enroll_evidence").style.display = "block";
});

document.getElementById("enroll_witness_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("enroll_witness").style.display = "block";
});

document.getElementById("enroll_victim_menu").addEventListener("click", function() {
    var containers = document.getElementsByClassName("container");
    for (var i = 0; i < containers.length; i++) {
        containers[i].style.display = "none";
    }
    document.getElementById("enroll_victim").style.display = "block";
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("police_investigation_form").addEventListener('submit', function(e) {
        document.getElementById("investigation_table").style.display = "block";
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/get_investigation_list', formData)
        .then(function(response) {
            document.getElementById("investigation_table_body").innerHTML = response.data;
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

function select_investigation(button) {
    var tdElement = button.parentNode;
    var trElement = tdElement.parentNode;
    var investigation_id = trElement.querySelector('#investigation_id').innerText;
    const url = `/view_investigation_info?id=${encodeURIComponent(investigation_id)}`;
    window.open(url, '_blank', 'width=700,height=800,left=400,top=400');   
}

// ? 아이콘 클릭시 증거물 타입 설명
function toggleTooltip(id) {
    var tooltip = document.getElementById(id);
    if (tooltip.style.display === "none" || tooltip.style.display === "") {
        tooltip.style.display = "block";
    } else {
        tooltip.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("enroll_evidence_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/enroll_evidence', formData)
        .then(function(response) {
            swal.fire({
                html: response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                icon: "info",
                showCloseButton: true,
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

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("enroll_witness_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/enroll_witness', formData)
        .then(function(response) {
            swal.fire({
                html: response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                icon: "info",
                showCloseButton: true,
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

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById("enroll_victim_form").addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);

        axios.post('/enroll_victim', formData)
        .then(function(response) {
            swal.fire({
                html: response.data.replace(/&lt;br&gt;/g, '<br>').replace(/&lt;/g, '<').replace(/&gt;/g, '>'),
                icon: "info",
                showCloseButton: true,
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