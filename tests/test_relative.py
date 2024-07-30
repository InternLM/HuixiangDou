def test_reject(retriever: Retriever, sample: str = None):
    """Simple test reject pipeline."""
    if sample is None:
        real_questions = [
            'SAM 10个T 的训练集，怎么比比较公平呢~？速度上还有缺陷吧？',
            '想问下，如果只是推理的话，amp的fp16是不会省显存么，我看parameter仍然是float32，开和不开推理的显存占用都是一样的。能不能直接用把数据和model都 .half() 代替呢，相比之下amp好在哪里',  # noqa E501
            'mmdeploy支持ncnn vulkan部署么，我只找到了ncnn cpu 版本',
            '大佬们，如果我想在高空检测安全帽，我应该用 mmdetection 还是 mmrotate',
            '请问 ncnn 全称是什么',
            '有啥中文的 text to speech 模型吗?',
            '今天中午吃什么？',
            'huixiangdou 是什么？',
            'mmpose 如何安装？',
            '使用科研仪器需要注意什么？'
        ]
    else:
        with open(sample) as f:
            real_questions = json.load(f)

    for example in real_questions:
        relative, _ = retriever.is_relative(example)

        if relative:
            logger.warning(f'process query: {example}')
        else:
            logger.error(f'reject query: {example}')

        if sample is not None:
            if relative:
                with open('workdir/positive.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')
            else:
                with open('workdir/negative.txt', 'a+') as f:
                    f.write(example)
                    f.write('\n')

    empty_cache()
