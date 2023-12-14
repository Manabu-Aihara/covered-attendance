// お前はもう、宣言されている
// const selectArea = document.getElementsByClassName('form-control')[0];
const selectChildren = selectArea.options;
// console.log(selectChildren);

// 開始時刻・終了時刻
const timeForms = document.getElementsByClassName('restrict-form');
// 入力制限処理トグル関数
const toggleRestrictState = (flag) => {
  if (flag == true) {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = true;
      timeForms[i].style.backgroundColor = "gainsboro";
    }
  } else {
    for (let i = 0; i < timeForms.length; i++) {
      timeForms[i].readOnly = false;
      timeForms[i].style.backgroundColor = "";
    }
  }
}

const startTimeForm = timeForms[0];
const endTimeForm = timeForms[1];

// 早退における、終業時刻の入力を促す
const encourageInput = () => {
  if ((selectChildren.selectedIndex - 1) === 2) {
    if (endTimeForm.value === "") {
      globalFlag = false;
      alert("終業時刻を入力してください。");
      endTimeForm.focus();
      return globalFlag;
    } else {
      globalFlag = true;
      return globalFlag;
    }
  }
}

// Param: diffNum 何時間後
const reflectTimeForm = (diffNum) => {
  /**
   * input type=date:値の変更の感知にはinput
   */
  startTimeForm.addEventListener('input', () => {
    let [h, m] = startTimeForm.value.split(':');
    // console.log(0 + h);
    if (h < 10) {
      const oneDigit = Number(h) + diffNum
      /**
       * 数字を指定した桁数まで0埋めする
          https://gray-code.com/javascript/fill-numbers-with-zeros/
       */
      endTimeForm.value = `${oneDigit.toString().padStart(2, '0')}:${m}`;
    } else {
      endTimeForm.value = `${Number(h) + diffNum}:${m}`;
    }
  });
}

const restrictCollection = () => {
  console.log("Called!")
  console.log(selectChildren.selectedIndex - 1);

  // for(let option in selectChildren){
  //   console.log(option.selectedIndex);
  for (let i = 0; i < selectChildren.length; i++) {
    if ((selectChildren.selectedIndex - 1) === 3 || (selectChildren.selectedIndex - 1) === 5 || (selectChildren.selectedIndex - 1) === 7 || (selectChildren.selectedIndex - 1) === 8 || (selectChildren.selectedIndex - 1) === 9 || (selectChildren.selectedIndex - 1) === 17 || (selectChildren.selectedIndex - 1) === 18 || (selectChildren.selectedIndex - 1) === 19 || (selectChildren.selectedIndex - 1) === 20) {
      toggleRestrictState(true);
    } else if ((selectChildren.selectedIndex - 1) === 10 || (selectChildren.selectedIndex - 1) === 13) {
      toggleRestrictState(false);
      reflectTimeForm(1);
    } else if ((selectChildren.selectedIndex - 1) === 11 || (selectChildren.selectedIndex - 1) === 14) {
      toggleRestrictState(false);
      reflectTimeForm(2);
    } else if ((selectChildren.selectedIndex - 1) === 12 || (selectChildren.selectedIndex - 1) === 15) {
      toggleRestrictState(false);
      reflectTimeForm(3);
    } else {
      toggleRestrictState(false);
    }
  }
}

selectForm.addEventListener('change', restrictCollection);
