"""Task Advisor - Provides AI recommendations for specific Phase 1 tasks."""
import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from config import get_settings

logger = logging.getLogger(__name__)


TASK_RECOMMENDATIONS = {
    "Optimize LinkedIn profile with counselor-focused positioning": """
**LinkedIn Profile Optimization for Counselor Outreach:**

1. **Headline:** Position yourself as a founder/builder, not a salesperson
   - Example: "Building AI tools to amplify counselor expertise | StemPro Academy"
   - Avoid: "Selling AI platform to counselors"

2. **About Section:** Lead with the problem you're solving
   - Start with: "Independent counselors spend 60% of their time on admin work..."
   - Position TargetAI as the solution that respects their expertise
   - Include your "counselor-first" philosophy

3. **Featured Section:** Add credibility signals
   - Link to any counselor testimonials
   - Share your Phase 1 approach (transparent, pilot-based)
   - Include ethical AI positioning

4. **Activity:** Post 1-2x/week about counselor challenges
   - Share insights from conversations
   - Ask questions to counselor community
   - Build credibility through value-first content

**Red Flags to Avoid:**
- Don't mention "AI will replace counselors"
- Avoid heavy sales language
- Don't oversell features that aren't built yet
""",

    "Build target list of 50 counselors matching selection criteria": """
**Building Your Target Counselor List:**

1. **LinkedIn Search Strategy:**
   - Search: "Independent Educational Consultant" + "IECA"
   - Look for: 500+ connections, recent activity, professional headshot
   - Filter by location if testing regional differences

2. **Selection Criteria (from scoring rubric):**
   - Active caseload (10+ students annually)
   - Tech-savvy (uses CRM, Google Workspace, Zoom)
   - Independent or small firm (<5 people)
   - Ethical signals (no outcome guarantees in profile)
   - Industry presence (posts content, IECA member)

3. **Qualification Questions:**
   - Check their "Experience" section for years in counseling
   - Review their posts for tech comfort level
   - Look for IECA certification badge
   - Check if they mention specific tools they use

4. **Build Your Spreadsheet:**
   Columns: Name, LinkedIn URL, Score (1-15), Region, Specialization, Notes
   - Prioritize scores 12+ for first wave
   - Aim for geographic diversity
   - Mix of veteran (5+ yrs) and newer counselors

**Where to Find Counselors:**
- IECA member directory: https://www.iecaonline.com
- LinkedIn hashtags: #IECA #CollegeCounseling #IEC
- HECA members as secondary targets
""",

    "Send 20 connection requests with personalized notes": """
**Personalized LinkedIn Connection Strategy:**

1. **Before Sending:**
   - Engage with their content for 1-2 weeks first
   - Leave thoughtful comments on 2-3 posts
   - Build "soft recognition" before the ask

2. **Connection Message Template:**
   ```
   Hi [Name],

   I've been following your insights on [specific topic from their content].
   Your perspective on [specific thing they said] really resonated.

   I'm building counselor-first AI tools at StemPro Academy and would
   value your perspective. Would love to connect!

   - [Your name]
   ```

3. **Personalization Keys:**
   - Reference a SPECIFIC post or article they wrote
   - Mention their specialization (if they have one)
   - Avoid generic "I see we're in the same industry"

4. **Volume Strategy:**
   - Send 5 requests/day (not all 20 at once)
   - Vary your message slightly each time
   - Track which messages get best response

**Expected Response Rate:**
- Generic message: 5-10%
- Personalized with engagement: 20-30%
- Warm intro from mutual connection: 40-60%
""",

    "Engage with 10 counselor posts (meaningful comments)": """
**Meaningful Engagement Strategy:**

1. **What Makes a "Meaningful" Comment:**
   ✅ Good: "This is such an important point about [specific insight]. In my experience building tools for counselors, I've seen..."
   ❌ Bad: "Great post!" or "Agree!"

2. **Engagement Formula:**
   - Acknowledge their specific point
   - Add a complementary insight or question
   - Keep it under 3 sentences
   - Don't pitch your product

3. **Where to Find Quality Posts:**
   - Follow 20-30 counselors and check feed daily
   - Search #IECA #CollegeCounseling hashtags
   - Join IECA LinkedIn groups
   - Look for posts with 10+ comments (active discussions)

4. **Timing:**
   - Comment within 2 hours of post going live (better visibility)
   - Engage when counselors are active (usually 7-9am, 6-8pm EST)

5. **Track Your Engagement:**
   Keep a simple log: Post URL, Your Comment, Did They Respond?
   - If they respond, follow up with value
   - Consider connecting after 2-3 quality exchanges

**Remember:** You're building relationships, not trying to sell immediately
""",

    "Draft and publish first LinkedIn thought leadership post": """
**First LinkedIn Thought Leadership Post:**

1. **Topic Ideas That Resonate with Counselors:**
   - "Why AI in counseling isn't about replacement, it's about amplification"
   - "The ethical line: What AI should (and shouldn't) do in college admissions"
   - "How independent counselors can compete with large firms using smart tools"

2. **Post Structure:**
   - Hook (first line): Start with a relatable counselor pain point
   - Problem: Expand on the challenge (60% time on admin, not students)
   - Perspective: Your unique take on AI ethics in this space
   - Soft CTA: "Building something in this space—DM if you'd like early access"

3. **Example Opening Lines:**
   - "I asked 15 independent counselors: 'What would you do with 10 extra hours/week?'"
   - "There's a right way and a wrong way to use AI in college counseling..."
   - "Why I'm building an AI tool that refuses to write college essays"

4. **Format Tips:**
   - Use line breaks (1-2 sentence paragraphs)
   - Include a personal story or conversation
   - End with a question to drive comments
   - NO SALESY LANGUAGE

5. **Timing:**
   - Post Tuesday-Thursday, 8-10am EST (best engagement)
   - Respond to all comments within 24 hours
   - Share in relevant LinkedIn groups

**Goal:** Position yourself as a thoughtful builder, not a vendor
""",

    "Prepare demo environment with realistic sample data": """
**Demo Environment Setup:**

1. **Create Realistic Sample Students:**
   - 3-4 demo student profiles with diverse backgrounds
   - Different academic levels (high achiever, mid-tier, struggling)
   - Various interests (STEM, humanities, arts)
   - Include realistic notes and interaction history

2. **Sample Data to Include:**
   - GPA, test scores, activities (realistic ranges)
   - 2-3 college lists in progress
   - Meeting notes from "past sessions"
   - Essay topics/drafts (appropriate for demo)

3. **Demo Script Preparation:**
   - 5-minute walkthrough flow
   - Key features to highlight (based on their pain points)
   - Prepared answers to common objections
   - "Quick win" moment (generate something useful in demo)

4. **Technical Checklist:**
   - Test all features work smoothly
   - Pre-load data so no waiting during demo
   - Have backup plan if internet/platform issues
   - Screen share settings optimized

5. **Practice:**
   - Record yourself doing demo
   - Time it (should be 30-40 min max)
   - Identify awkward transitions
   - Prepare 3-5 common Q&A responses

**Remember:** Demo should feel natural, not scripted. Focus on THEIR workflow, not your features.
"""
}


async def get_task_recommendation(task_description: str) -> str:
    """Get AI recommendation for a specific task.

    Args:
        task_description: The task to get recommendations for

    Returns:
        AI-generated recommendation
    """
    # Check if we have a pre-written recommendation
    if task_description in TASK_RECOMMENDATIONS:
        return TASK_RECOMMENDATIONS[task_description]

    # Otherwise use AI to generate recommendation
    settings = get_settings()
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=settings.anthropic_api_key,
        temperature=0.7,
    )

    system_prompt = """You are an expert advisor for TargetAI's Phase 1 launch.

Your role is to provide practical, actionable recommendations for executing Phase 1 tasks.

Context:
- Phase 1 is a "Counselor Credibility Pilot" (8 weeks)
- Goal: Onboard 10-15 carefully selected independent counselors
- Approach: Founder-led, highly personalized, quality over quantity
- Ethics: No AI essay writing, no acceptance guarantees, counselor-first philosophy

Provide specific, tactical advice that helps the founder execute this task effectively.
Include examples, templates, or step-by-step guidance where helpful."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Provide detailed recommendations for this Phase 1 task:\n\n{task_description}")
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Error getting AI recommendation: {e}")
        return f"Unable to generate specific recommendation for this task. Please refer to the Phase 1 Action Plan document for guidance on: {task_description}"
