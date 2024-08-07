//script.js

function selectUser(userType) {
    document.getElementById('selectedUser').value = userType;
    document.getElementById('loginForm').style.display = 'block';
}

document.addEventListener("DOMContentLoaded", function() {
    // Flask에서 전달한 메시지가 있을 경우 경고창 띄우기
    var message = "{{ message }}";
    if (message && message.includes("일치하지 않습니다")) {
        alert("다시 입력하세요.");
    }
});