
// お前はもう、宣言されている
// const bottomForm = document.getElementById('form-bottom');
const JudgeButton = document.getElementsByClassName('judgement');

// JudgeButton[0].addEventListener('click', (e) => {
//   let ModalSubmit_ok = new ModalAppear(backArea[0], modalElement);
//   ModalSubmit_ok.appearModalSubmit("承認します。", "承認されました。");
//   console.log(bottomForm[0]);
//   bottomForm[0].submit();
//   e.preventDefault();
// });
// JudgeButton[1].addEventListener('click', (e) => {
//   let ModalSubmit_ok = new ModalAppear(backArea[0], modalElement);
//   ModalSubmit_ok.appearModalSubmit("未承認にします。", "未承認です。");
//   console.log(bottomForm[1]);
//   bottomForm[1].submit();
//   e.preventDefault();
// });
globalFlag = true;
const ModalSubmit_ok = new ModalAppear(backArea[0], modalElement, JudgeButton[0], bottomForm[0]);
ModalSubmit_ok.callModal("承認します。", "承認されました。");
const ModalSubmit_ng = new ModalAppear(backArea[0], modalElement, JudgeButton[1], bottomForm[1]);
ModalSubmit_ng.callModal("未承認にします。", "未承認です。");
