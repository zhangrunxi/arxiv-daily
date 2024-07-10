from datetime import datetime, timedelta, date
import requests
import json
import arxiv
import os

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"

def get_authors(authors, first_author = False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output
def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output    

def get_daily_papers(topic,query="slam", max_results=20):
    """
    @param topic: str
    @param query: str
    @return paper_with_code: dict
    """

    # output 
    content = dict() 
    content_to_web = dict()

    # content
    output = dict()
    
    search_engine = arxiv.Search(
        query = query,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.SubmittedDate
    )

    cnt = 0
    # 计算时间范围
    end_date = datetime.now()  # 当前时间
    start_date = end_date - timedelta(days=7)  # 最近 7 天的开始时间
    print(start_date)
    for result in search_engine.results():

        paper_id            = result.get_short_id()
        paper_title         = result.title
        paper_url           = result.entry_id
        code_url            = base_url + paper_id
        paper_abstract      = result.summary.replace("\n"," ")
        paper_authors       = get_authors(result.authors)
        paper_first_author  = get_authors(result.authors,first_author = True)
        primary_category    = result.primary_category
        publish_time        = result.published.date()
        update_time         = result.updated.date()
        comments            = result.comment
       
        print(type(result.published)) 
        submitted_date = result.published.strftime("%Y-%m-%dT%H:%M:%SZ")
        if start_date > submitted_date:
            continue

        print(paper_id, paper_title, publish_time)


      
        print("Time = ", update_time ,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]    

        try:
            r = requests.get(code_url).json()
            # source code link
            if "official" in r and r["official"]:
                cnt += 1
                repo_url = r["official"]["url"]
                content[paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[![arxiv](https://img.shields.io/badge/arXiv-{paper_id}-b31b1b.svg)]({paper_url})|**[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)]({repo_url})**|\n"
                content_to_web[paper_key] = f"- {update_time}, **{paper_title}**, {paper_first_author} et.al., Paper: [{paper_url}]({paper_url}), Code: **[{repo_url}]({repo_url})**"

            else:
                content[paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[![arxiv](https://img.shields.io/badge/arXiv-{paper_id}-b31b1b.svg)]({paper_url})|null|\n"
                content_to_web[paper_key] = f"- {update_time}, **{paper_title}**, {paper_first_author} et.al., Paper: [{paper_url}]({paper_url})"

            # TODO: select useful comments
            comments = None
            if comments != None:
                content_to_web[paper_key] = content_to_web[paper_key] + f", {comments}\n"
            else:
                content_to_web[paper_key] = content_to_web[paper_key] + f"\n"

        except Exception as e:
            print(f"exception: {e} with id: {paper_key}")

    data = {topic:content}
    data_web = {topic:content_to_web}
    return data,data_web 

def update_json_file(filename,data_all):
    with open(filename,"r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)
            
    json_data = m.copy() 
    
    # update papers in each keywords         
    for data in data_all:
        for keyword in data.keys():
            papers = data[keyword]

            if keyword in json_data.keys():
                json_data[keyword].update(papers)
            else:
                json_data[keyword] = papers

    with open(filename,"w") as f:
        json.dump(json_data,f)
    
def json_to_md(filename,md_filename,to_web = False, use_title = True):
    """
    @param filename: str
    @param md_filename: str
    @return None
    """
    
    DateNow = date.today()
    DateNow = str(DateNow)
    DateNow = DateNow.replace('-','.')
    
    with open(filename,"r") as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    # clean README.md if daily already exist else create it
    with open(md_filename,"w+") as f:
        pass

    # write data into README.md
    with open(md_filename,"a+") as f:

        if (use_title == True) and (to_web == True):
            f.write("---\n" + "layout: default\n" + "---\n\n")

        if use_title == True:
            f.write("## Updated on " + DateNow + "\n\n")
        else:
            f.write("> Updated on " + DateNow + "\n\n")
        
        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            # the head of each part
            f.write(f"## {keyword}\n\n")

            if use_title == True :
                if to_web == False:
                    f.write("|Publish Date|Title|Authors|PDF|Code|\n" + "|---|---|---|---|---|\n")
                else:
                    f.write("| Publish Date | Title | Authors | PDF | Code |\n")
                    f.write("|:---------|:-----------------------|:---------|:------|:------|\n")

            # sort papers by date
            day_content = sort_papers(day_content)
        
            for _,v in day_content.items():
                if v is not None:
                    f.write(v)

            f.write(f"\n")

    print("finished")        

 

if __name__ == "__main__":

    data_collector = []
    data_collector_web= []
    
    keywords = dict()
    keywords["Autonomous_Driving_Planning"]  = "abs:autonomous AND abs:driving AND abs:planning"
    keywords["Autonomous_Driving_Prediction"]  = "abs:autonomous AND abs:driving AND abs:prediction OR abs:predict"
    keywords["Autonomous_Driving_Decision"]  = "abs:autonomous AND abs:driving AND abs:decision OR abs:decider"
    keywords["Autonomous_Driving_E2E"]  = "abs:autonomous AND abs:driving AND abs:end AND abs:to AND abs:end"
    keywords["Autonomous_Driving_LLM"]  = "abs:autonomous AND abs:driving AND abs:llm"
    keywords["Autonomous_Driving_RL"]  = "abs:autonomous AND abs:driving AND abs:reinforcement AND abs:learning"

    for topic,keyword in keywords.items():
 
        # topic = keyword.replace("\"","")
        print("Keyword: " + topic)

        data,data_web = get_daily_papers(topic, query = keyword, max_results = 10)
        data_collector.append(data)
        data_collector_web.append(data_web)

        print("\n")

    # 1. update README.md file
    json_file = "adas-arxiv-daily.json"
    md_file   = "README.md"
    daily_md_file = f"arxivs/{datetime.now().strftime('%Y%m%d')}.md"
    # update json data
    update_json_file(json_file,data_collector)
    # json data to markdown
    json_to_md(json_file,md_file)
    json_to_md(json_file, daily_md_file)

    # 2. update docs/index.md file
    json_file = "./docs/adas-arxiv-daily-web.json"
    md_file   = "./docs/index.md"
    # update json data
    update_json_file(json_file,data_collector)
    # json data to markdown
    json_to_md(json_file, md_file, to_web = True)

    # 3. Update docs/wechat.md file
    json_file = "./docs/adas-arxiv-daily-wechat.json"
    md_file   = "./docs/wechat.md"
    # update json data
    update_json_file(json_file, data_collector_web)
    # json data to markdown
    json_to_md(json_file, md_file, to_web=False, use_title= False)
