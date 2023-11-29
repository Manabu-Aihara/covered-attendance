const notificationDateList = document.getElementsByClassName('notice-date');
// お前はもう、宣言されている
// const yearMonthDate = document.getElementsByClassName('month-calender')[0];
// const trRows = document.getElementsByClassName('body-tr');

// 申請一覧pathname
const tail_d = /\d+$/;
// 承認者閲覧pathname
const chargePath = /approval-list\/charge*$/;
const appearRows = document.getElementsByClassName('appear');

const showRowsByNotificationDate = () => {
  console.log(yearMonthDate.value);
  for(let i = 0; i < notificationDateList.length; i++){
    // console.log(notificationDateList[i].textContent.match(/^\d{4}-?\d{2}/)[0]);
    // ['2023-08', index: 0, input: '2023-08-17 10:17:04', groups: undefined]なので[0]
    if(notificationDateList[i].textContent.match(/^\d{4}-?\d{2}/)[0] !== yearMonthDate.value){
      trRows[i].style.display = "none";
    }else{
      // 承認者閲覧一覧ページなら
      if(chargePath.test(location.pathname) && notificationDateList[i].textContent.match(/^\d{4}-?\d{2}/)[0] !== yearMonthDate.value){
        console.log("ここ通る");
        for(let j = 0; j < appearRows.length; j++){
          appearRows[j].style.display = "none";
        }
      }else if(tail_d.test(location.pathname)){
        trRows[i].style.display = "table-row";
      }
    }

    if(yearMonthDate.value === ""){
      for(let i = 0; i < trRows.length; i++){
        trRows[i].style.display = "table-row";
      }
    }
  }
}

yearMonthDate.addEventListener('change', showRowsByNotificationDate);

// 申請一覧画面ならデフォルトで今月
if(tail_d.test(location.pathname)){
  const now = new Date();
  const nowYM = `${now.getFullYear()}-${now.getMonth() + 1}`;
  window.addEventListener('load', () => {
    yearMonthDate.value = nowYM;
    showRowsByNotificationDate();
  });
}else if(chargePath.test(location.pathname)){
  window.addEventListener('load', () => {
    yearMonthDate.value = "";
  });  
}
