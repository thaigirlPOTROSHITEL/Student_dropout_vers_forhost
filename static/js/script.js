document.addEventListener('DOMContentLoaded', function() {
    const MAGISTR_SUBJECTS = ['Вэб-технологии в бизнесе', 'Математические основы искусственного интеллекта', 'Машинное обучение', 'Программирование на Python', 'Проектный практикум 1', 'Философия и методология науки', 'Квалиметрия изображений', 'Математические модели и алгоритмы', 'Производственная практика, научно-исследовательская работа', 'Технологии цифровой подготовки публикаций', 'Учебно-исследовательская общенаучная работа', 'Физические основы цифровой печати', 'Математическое моделирование', 'Программирование на PYTHON', 'Психология обработки сенсорной информации', 'Типографика и макетирование', 'Физические явления в репродукционных технологиях', 'Цифровые компетенции в научной деятельности', 'Введение в проблематику создания ракетных комплексов', 'Инженерно-техническая реализация систем управления', 'Методы и алгоритмы проектирования программного обеспечения систем управления', 'Промышленные сети и защищённая передача данных', 'Технологии интернета вещей', 'Учебная практика, научно-исследовательская работа', 'Магистрально-модульные системы реального времени', 'Управление в технических системах', 'Здоровье человека и интеллектуальные информационные системы и технологии здоровьесбережения', 'Методы анализа данных и статистики', 'Методы и аппаратно-программные комплексы функциональных исследований', 'Научный семинар по актуальным проблемам науки и производства', 'Разработка приложений на языке  PYTHON', 'Сенсорика для медицины', 'Программирование на Java', 'Программная инженерия', 'Управление программными проектами', 'Математическое моделирование радиотехнических устройств и систем', 'Методы и средства цифровой обработки сигналов', 'Программирование для встраиваемых систем', 'Радиотехнические системы передачи информации', 'Схемотехника современной радиоэлектроники', 'Теория и техника измерений в радиоэлектронике', 'Интеллектуальные и мультиагентные системы', 'Компьютерный анализ и интерпретация данных', 'Методы и средства построения программных систем', 'Методы оптимизации', 'Системы цифровой экономики', 'Современные проблемы информатики и вычислительной техники (научный семинар)', 'Технологии командной разработки программного обеспечения (ПО)', 'Аналитика больших данных для бизнеса', 'Инновации в бизнесе и ИТ', 'Практическое предпринимательство', 'Управление жизненным циклом информационных систем', 'Философские проблемы науки и техники', 'Актуальные проблемы философии и истории науки', 'Математические методы теории сигналов и систем', 'Методы контроля защищенности информации ИСПДн, ГИС и значимых объектов КИИ', 'Организация защищенных сетевых коммуникаций в ИСПДн, ГИС и на объектах КИИ', 'Основы научного исследования', 'Профессиональный иностранный язык', 'Управление информационной безопасностью ИСПДн, ГИС и значимых объектов КИИ', 'Управление проектами в области информационной  безопасности', 'Базы данных', 'Взаимодействие в команде', 'Карьерное развитие молодого специалиста', 'Разработка приложений', 'Современные финансовые технологии', 'Управление собой', 'Инжиниринг данных', 'Иностранный язык в сфере делового и профессионального общения', 'Операционная система Linux', 'Бизнес коммуникация на английском', 'Математические основы анализа данных', 'Математические основы машинного обучения', 'Методология научных исследований', 'Разработка веб-приложений'];
    
    const BAK_SPEC_SUBJECTS = [ 'Иностранный язык', 'Информационные технологии и сервисы', 'История России', 'Математика', 'Основы проектной деятельности', 'Основы российской государственности', 'Прикладная физическая культура', 'Программирование', 'Физика', 'Элементарные основы физики', 'Основы личностного роста', 'Введение в специальность', 'Векторный анализ', 'Компьютерная и инженерная графика', 'Алгебра и геометрия', 'Алгебра', 'Геометрия', 'Информатика', 'Математический анализ', 'Алгоритмизация и программирование', 'Алгебра, геометрия и теория дифференциальных уравнений', 'Инженерная и компьютерная графика', 'Общевоинские уставы ВС РФ', 'Строевая подготовка', 'Дискретная математика и математическая логика', 'Основы редактирования', 'Русский язык', 'Современный русский язык', 'Стилистика русского языка', 'Язык делового общения'];
    
    const GRADES = ['5', '4', '3', '2', 'Зачёт', 'Незачёт', 'Недопуск', 'Недосдал', 'Неуважительная причина'];

    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.prediction-form').forEach(f => f.classList.remove('active'));

            this.classList.add('active');

            const formId = `${this.dataset.tab}-form`;
            document.getElementById(formId).classList.add('active');
        });
    });

    document.getElementById('m_add-subject').addEventListener('click', () => {
        addSubject('m', MAGISTR_SUBJECTS);
    });

    document.getElementById('b_add_subject').addEventListener('click', () => {
        addSubject('b', BAK_SPEC_SUBJECTS);
    });

    function addSubject(prefix, subjectsList) {
        const container = document.getElementById(`${prefix}_subjects_container`);
        const subjectId = Date.now();

        const subjectDiv = document.createElement('div');
        subjectDiv.className = 'subject-entry';
        subjectDiv.dataset.id = subjectId;

        const subjectFields = document.createElement('div');
        subjectFields.className = 'subject-fields';

        const createFormGroup = (labelText, elementType, name, options = null) => {
            const group = document.createElement('div');
            group.className = 'form-group';

            const label = document.createElement('label');
            label.textContent = labelText;
            group.appendChild(label);

            let element;
            if (elementType === 'select') {
                element = document.createElement('select');
                element.name = name;
                element.required = true;
                element.className = 'subject-select'; // Добавляем класс для стилизации

                if (options) {
                    options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = option;
                        element.appendChild(optionElement);
                    });
                }
            } else {
                element = document.createElement('input');
                element.type = elementType;
                element.name = name;
                element.required = true;

                if (elementType === 'number') {
                    element.min = name.includes('score') ? '0' : '0';
                    element.max = name.includes('score') ? '100' : '50';
                }
            }

            group.appendChild(element);
            return group;
        };

        subjectFields.appendChild(
            createFormGroup('Дисциплина:', 'select', `${prefix}_subject_name[]`, subjectsList)
        );

        subjectFields.appendChild(
            createFormGroup('Оценка:', 'select', `${prefix}_subject_grade[]`, GRADES)
        );

        subjectFields.appendChild(
            createFormGroup('Баллы (0-100):', 'number', `${prefix}_subject_score[]`)
        );

        subjectFields.appendChild(
            createFormGroup('Пересдачи (0-50):', 'number', `${prefix}_subject_retakes[]`)
        );

        subjectDiv.appendChild(subjectFields);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn-remove-subject';
        removeBtn.dataset.id = subjectId;
        removeBtn.textContent = '×';
        subjectDiv.appendChild(removeBtn);

        container.appendChild(subjectDiv);
    }

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('btn-remove-subject')) {
            const subjectId = e.target.dataset.id;
            const subjectElement = document.querySelector(`.subject-entry[data-id="${subjectId}"]`);
            if (subjectElement) {
                subjectElement.remove();
            }
        }
    });
    document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const fileInputs = this.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.value = '';
        });
    });
});

   

    const forms = document.querySelectorAll('.prediction-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                alert('Пожалуйста, заполните все обязательные поля корректно');
            }
        });
    });

    function validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required]');

        inputs.forEach(input => {
            if (!input.value) {
                markInvalid(input, 'Это поле обязательно для заполнения');
                isValid = false;
            } else if (input.type === 'number' && isNaN(input.value)) {
                markInvalid(input, 'Введите число');
                isValid = false;
            } else if (input.type === 'text' && input.pattern && !new RegExp(input.pattern).test(input.value)) {
                markInvalid(input, 'Неверный формат');
                isValid = false;
            } else {
                markValid(input);
            }
        });

        return isValid;
    }

    function markInvalid(element, message) {
        element.style.borderColor = '#e74c3c';
        if (!element.nextElementSibling?.classList?.contains('error-message')) {
            const errorMsg = document.createElement('div');
            errorMsg.className = 'error-message';
            errorMsg.textContent = message;
            errorMsg.style.color = '#e74c3c';
            errorMsg.style.fontSize = '0.8rem';
            errorMsg.style.marginTop = '0.3rem';
            element.insertAdjacentElement('afterend', errorMsg);
        }
    }

    function markValid(element) {
        element.style.borderColor = '';
        if (element.nextElementSibling?.classList?.contains('error-message')) {
            element.nextElementSibling.remove();
        }
    }

    const csvUploads = document.querySelectorAll('input[type="file"]');
    csvUploads.forEach(upload => {
        upload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const form = this.closest('form');
                if (form) {
                    form.submit();
                }
            }
        });
    });
    function downloadExample(educationLevel) {
        window.location.href = `/download_example/${educationLevel}`;
    }

    document.querySelectorAll('[onclick^="downloadExample"]').forEach(btn => {
        btn.addEventListener('click', function() {
            const educationLevel = this.getAttribute('onclick').match(/downloadExample\('(\w+)'\)/)[1];
            downloadExample(educationLevel);
        });
    });
});
